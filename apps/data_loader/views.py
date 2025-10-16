"""
Views for data_loader app
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def data_loader_info(request):
    """Información básica del sistema de carga de datos"""
    return Response({
        'status': 'success',
        'message': 'Sistema de carga de datos funcionando',
        'features': [
            'Procesamiento de archivos Excel',
            'Validación de datos',
            'Carga masiva de información'
        ]
    })


# Add more views for Excel upload and processing as needed
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def upload_excel(request):
#     """Upload and process Excel file"""
#     pass