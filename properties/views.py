from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Property
from .serializers import PropertySerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def property_list_create(request):
    if request.user.role not in ('agent', 'owner'):
        return Response(
            {'detail': 'Only agents and property owners can manage listings.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'GET':
        properties = Property.objects.filter(agent=request.user)

        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price:
            properties = properties.filter(price__gte=min_price)
        if max_price:
            properties = properties.filter(price__lte=max_price)

        property_type = request.GET.get('property_type')
        if property_type:
            properties = properties.filter(property_type=property_type)

        listing_type = request.GET.get('listing_type')
        if listing_type:
            properties = properties.filter(listing_type=listing_type)

        location = request.GET.get('location')
        if location:
            properties = (
                properties.filter(city_state__icontains=location)
                | properties.filter(address__icontains=location)
            )

        serializer = PropertySerializer(properties, many=True, context={'request': request})
        return Response(serializer.data)

    serializer = PropertySerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(agent=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def property_delete(request, pk):
    try:
        prop = Property.objects.get(pk=pk, agent=request.user)
    except Property.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    prop.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def property_update_price(request, pk):
    try:
        prop = Property.objects.get(pk=pk, agent=request.user)
    except Property.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    price = request.data.get('price')
    if price is None:
        return Response({'price': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

    prop.price = price
    prop.save()
    return Response(PropertySerializer(prop, context={'request': request}).data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def property_update(request, pk):
    try:
        prop = Property.objects.get(pk=pk, agent=request.user)
    except Property.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = PropertySerializer(prop, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
