from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F, Q, Sum, DecimalField, ExpressionWrapper
from django.db import transaction
from .models import Medicine, InventoryTransaction, PrescriptionDispense
from .serializers import (
    MedicineSerializer,
    InventoryTransactionSerializer,
    PrescriptionDispenseSerializer,
    LowStockAlertSerializer
)
from .permissions import IsPharmacyStaff, CanDispensePrescription, CanImportInvoices
from .ocr import OCRService, naive_line_parser
from datetime import date


class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [IsPharmacyStaff]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'generic_name', 'manufacturer']
    ordering_fields = ['name', 'current_stock', 'created_at']

    def get_queryset(self):
        qs = Medicine.objects.all()
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(generic_name__icontains=search) |
                Q(manufacturer__icontains=search)
            )
        ordering = self.request.query_params.get('ordering')
        if ordering:
            qs = qs.order_by(ordering)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        meds = Medicine.objects.filter(current_stock__lte=F('reorder_level'), is_active=True)
        alerts = [{
            'id': m.id,
            'name': m.name,
            'category': m.category,
            'current_stock': m.current_stock,
            'reorder_level': m.reorder_level,
            'stock_status': m.stock_status,
            'stock_deficit': m.reorder_level - m.current_stock
        } for m in meds]
        serializer = LowStockAlertSerializer(alerts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        meds = Medicine.objects.filter(current_stock=0, is_active=True)
        serializer = self.get_serializer(meds, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def transaction_history(self, request, pk=None):
        medicine = self.get_object()
        transactions = medicine.transactions.all()
        serializer = InventoryTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='add_stock')
    def add_stock(self, request, pk=None):
        medicine = self.get_object()
        try:
            qty = int(request.data.get('quantity') or 0)
        except Exception:
            return Response({'detail': 'Invalid quantity.'}, status=status.HTTP_400_BAD_REQUEST)
        if qty < 1:
            return Response({'detail': 'Quantity must be at least 1.'}, status=status.HTTP_400_BAD_REQUEST)

        batch = request.data.get('batch_number') or ''
        exp = request.data.get('expiry_date') or None
        exp_date = None
        if exp:
            try:
                exp_date = date.fromisoformat(str(exp))
            except Exception:
                exp_date = None

        InventoryTransaction.objects.create(
            medicine=medicine,
            transaction_type='STOCK_IN',
            quantity=qty,
            batch_number=batch,
            expiry_date=exp_date,
            notes='Manual stock-in via add_stock endpoint',
            created_by=request.user,
        )
        medicine.refresh_from_db()
        return Response({'medicine': medicine.id, 'name': medicine.name, 'current_stock': medicine.current_stock, 'added': qty})


class InventoryTransactionViewSet(viewsets.ModelViewSet):
    queryset = InventoryTransaction.objects.all()
    serializer_class = InventoryTransactionSerializer
    permission_classes = [IsPharmacyStaff]
    filterset_fields = ['medicine', 'transaction_type', 'created_by']
    ordering_fields = ['created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def profit_summary(self, request):
        """Gross profit from dispensed items: revenue - cost of goods sold.
        Optional filters: start (YYYY-MM-DD), end (YYYY-MM-DD), medicine, pharmacist.
        """
        qs = InventoryTransaction.objects.filter(transaction_type='DISPENSED')

        start = request.query_params.get('start')
        end = request.query_params.get('end')
        medicine = request.query_params.get('medicine')
        pharmacist = request.query_params.get('pharmacist')

        if start:
            qs = qs.filter(created_at__date__gte=start)
        if end:
            qs = qs.filter(created_at__date__lte=end)
        if medicine:
            qs = qs.filter(medicine_id=medicine)
        if pharmacist:
            qs = qs.filter(created_by_id=pharmacist)

        revenue_expr = ExpressionWrapper(
            F('quantity') * F('medicine__selling_price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
        cogs_expr = ExpressionWrapper(
            F('quantity') * F('medicine__buying_price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )

        agg = qs.aggregate(revenue=Sum(revenue_expr), cogs=Sum(cogs_expr))
        revenue = agg.get('revenue') or 0
        cogs = agg.get('cogs') or 0
        profit = revenue - cogs

        return Response({
            'revenue': str(revenue),
            'cogs': str(cogs),
            'profit': str(profit),
            'count': qs.count(),
        })

    @action(detail=False, methods=['get'])
    def spend_summary(self, request):
        """Total money spent acquiring stock: sum(quantity * buying_price) for STOCK_IN.
        Optional filters: start (YYYY-MM-DD), end (YYYY-MM-DD), medicine, pharmacist.
        """
        qs = InventoryTransaction.objects.filter(transaction_type='STOCK_IN')

        start = request.query_params.get('start')
        end = request.query_params.get('end')
        medicine = request.query_params.get('medicine')
        pharmacist = request.query_params.get('pharmacist')

        if start:
            qs = qs.filter(created_at__date__gte=start)
        if end:
            qs = qs.filter(created_at__date__lte=end)
        if medicine:
            qs = qs.filter(medicine_id=medicine)
        if pharmacist:
            qs = qs.filter(created_by_id=pharmacist)

        spent_expr = ExpressionWrapper(
            F('quantity') * F('medicine__buying_price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
        agg = qs.aggregate(spent=Sum(spent_expr))
        spent = agg.get('spent') or 0

        return Response({
            'spent': str(spent),
            'count': qs.count(),
        })

    @action(detail=False, methods=['get'])
    def finance_overview(self, request):
        """Combined overview: revenue, cost of goods sold (COGS), profit, and money spent on stock.
        Uses DISPENSED transactions for revenue/COGS and STOCK_IN for spend.
        Optional filters: start (YYYY-MM-DD), end (YYYY-MM-DD), medicine, pharmacist.
        """
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        medicine = request.query_params.get('medicine')
        pharmacist = request.query_params.get('pharmacist')

        dispensed = InventoryTransaction.objects.filter(transaction_type='DISPENSED')
        stock_in = InventoryTransaction.objects.filter(transaction_type='STOCK_IN')

        for qs in (dispensed, stock_in):
            if start:
                qs = qs.filter(created_at__date__gte=start)
            if end:
                qs = qs.filter(created_at__date__lte=end)
            if medicine:
                qs = qs.filter(medicine_id=medicine)
            if pharmacist:
                qs = qs.filter(created_by_id=pharmacist)

        revenue_expr = ExpressionWrapper(
            F('quantity') * F('medicine__selling_price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
        cogs_expr = ExpressionWrapper(
            F('quantity') * F('medicine__buying_price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
        spent_expr = cogs_expr

        rev_agg = dispensed.aggregate(revenue=Sum(revenue_expr))
        cogs_agg = dispensed.aggregate(cogs=Sum(cogs_expr))
        spent_agg = stock_in.aggregate(spent=Sum(spent_expr))

        revenue = rev_agg.get('revenue') or 0
        cogs = cogs_agg.get('cogs') or 0
        profit = revenue - cogs
        spent = spent_agg.get('spent') or 0

        return Response({
            'revenue': str(revenue),
            'cogs': str(cogs),
            'profit': str(profit),
            'spent': str(spent),
            'dispensed_count': dispensed.count(),
            'stock_in_count': stock_in.count(),
        })

    @action(detail=False, methods=['post'], url_path='stock_in')
    def stock_in(self, request):
        """Create a STOCK_IN transaction for a given medicine.
        Expects: { medicine: <id>, quantity: <int>, buying_price?: "decimal", batch_number?: "", expiry_date?: "YYYY-MM-DD" }
        Returns: { transaction_id, medicine, name, added, current_stock, price_updated? }
        """
        payload = request.data or {}
        try:
            med_id = int(payload.get('medicine'))
            qty = int(payload.get('quantity') or 0)
        except Exception:
            return Response({'detail': 'Invalid medicine or quantity.'}, status=status.HTTP_400_BAD_REQUEST)

        if med_id <= 0 or qty < 1:
            return Response({'detail': 'medicine must be a valid id and quantity >= 1.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            med = Medicine.objects.get(pk=med_id)
        except Medicine.DoesNotExist:
            return Response({'detail': 'Medicine not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Optional buying price update
        price_updated = None
        bp = payload.get('buying_price')
        if bp not in (None, ''):
            try:
                from decimal import Decimal
                new_bp = Decimal(str(bp))
                if med.buying_price != new_bp:
                    med.buying_price = new_bp
                    med.save(update_fields=['buying_price'])
                    price_updated = str(new_bp)
            except Exception:
                pass

        batch = payload.get('batch_number') or ''
        exp = payload.get('expiry_date') or None
        exp_date = None
        if exp:
            try:
                exp_date = date.fromisoformat(str(exp))
            except Exception:
                exp_date = None

        inv = InventoryTransaction.objects.create(
            medicine=med,
            transaction_type='STOCK_IN',
            quantity=qty,
            batch_number=batch,
            expiry_date=exp_date,
            notes='Manual stock-in via stock_in endpoint',
            created_by=request.user,
        )
        med.refresh_from_db()

        resp = {
            'transaction_id': inv.id,
            'medicine': med.id,
            'name': med.name,
            'added': qty,
            'current_stock': med.current_stock,
        }
        if price_updated is not None:
            resp['price_updated'] = price_updated

        return Response(resp, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='parse_invoice', permission_classes=[CanImportInvoices])
    def parse_invoice(self, request):
        """Parse an uploaded invoice file (CSV/TXT passthrough or OCR) into structured lines.
        Returns: { lines: [{ name, quantity, buying_price, batch_number, expiry_date }] }
        """
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'detail': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        content = file_obj.read()
        filename = getattr(file_obj, 'name', '')
        text = OCRService.extract_text(content, filename)
        if not text:
            # Provide more actionable diagnostics
            import os
            lower = (filename or '').lower()
            if lower.endswith('.csv') or lower.endswith('.txt'):
                hint = 'File appears to be text/CSV but decoding failed. Ensure UTF-8 or CSV formatting.'
                provider = 'passthrough'
                model = None
            elif os.getenv('USE_GEMINI') == '1' and os.getenv('GEMINI_API_KEY'):
                provider = 'gemini'
                model = os.getenv('GEMINI_VISION_MODEL', 'gemini-1.5-flash')
                hint = 'Gemini OCR returned no text. Try clearer image/PDF or adjust GEMINI_VISION_MODEL to gemini-1.5-pro.'
            elif os.getenv('USE_AWS_TEXTRACT') == '1':
                provider = 'aws_textract'
                model = None
                hint = 'AWS Textract returned no text. Verify AWS credentials and document quality.'
            else:
                provider = 'unconfigured'
                model = None
                hint = 'OCR not configured. Provide CSV/TXT or set USE_GEMINI=1 with GEMINI_API_KEY.'

            return Response({
                'detail': 'Unable to extract text.',
                'provider': provider,
                'model': model,
                'filename': filename,
                'hint': hint,
            }, status=status.HTTP_400_BAD_REQUEST)

        lines = naive_line_parser(text)
        return Response({'lines': lines})

    @action(detail=False, methods=['post'], url_path='apply_invoice', permission_classes=[CanImportInvoices])
    def apply_invoice(self, request):
        """Apply parsed invoice lines as STOCK_IN transactions and optionally update buying prices.
        Expects: { lines: [{ medicine, quantity, buying_price?, batch_number?, expiry_date? }] }
        Returns: { created_count, price_updates: [{ medicine, name, buying_price }] }
        """
        payload = request.data or {}
        lines = payload.get('lines') or []
        if not isinstance(lines, list):
            return Response({'detail': 'Invalid payload: lines must be a list.'}, status=status.HTTP_400_BAD_REQUEST)

        created_count = 0
        price_updates = []

        for l in lines:
            try:
                med_id = int(l.get('medicine'))
                qty = int(l.get('quantity') or 0)
            except Exception:
                continue

            if med_id <= 0 or qty <= 0:
                continue

            try:
                med = Medicine.objects.get(pk=med_id)
            except Medicine.DoesNotExist:
                continue

            # Optional buying price update
            bp = l.get('buying_price')
            if bp not in (None, ''):
                try:
                    from decimal import Decimal
                    new_bp = Decimal(str(bp))
                    if med.buying_price != new_bp:
                        med.buying_price = new_bp
                        med.save(update_fields=['buying_price'])
                        price_updates.append({'medicine': med.id, 'name': med.name, 'buying_price': str(new_bp)})
                except Exception:
                    pass

            # Optional batch and expiry
            batch = l.get('batch_number') or ''
            exp = l.get('expiry_date') or None
            exp_date = None
            if exp:
                try:
                    exp_date = date.fromisoformat(str(exp))
                except Exception:
                    exp_date = None

            # Create STOCK_IN transaction (model will handle stock increment)
            InventoryTransaction.objects.create(
                medicine=med,
                transaction_type='STOCK_IN',
                quantity=qty,
                batch_number=batch,
                expiry_date=exp_date,
                notes='Imported via invoice',
                created_by=request.user,
            )
            created_count += 1

        return Response({'created_count': created_count, 'price_updates': price_updates})


class PrescriptionDispenseViewSet(viewsets.ModelViewSet):
    queryset = PrescriptionDispense.objects.all()
    serializer_class = PrescriptionDispenseSerializer
    permission_classes = [CanDispensePrescription]
    filterset_fields = ['medicine', 'pharmacist', 'prescription']
    ordering_fields = ['dispensed_at']

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
