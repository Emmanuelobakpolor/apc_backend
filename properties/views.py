from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db.models import F
from .models import Property, Inquiry, InquiryReply
from .serializers import PropertySerializer, InquirySerializer, InquiryReplySerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def property_listings(request):
    """All active listings — visible to every authenticated user."""
    properties = Property.objects.filter(status='active')

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


# ── Inquiry endpoints ────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_inquiry(request, pk):
    """Any authenticated user sends an inquiry about a property."""
    try:
        prop = Property.objects.get(pk=pk, status='available')
    except Property.DoesNotExist:
        return Response({'detail': 'Property not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = InquirySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(property=prop, sender=request.user)
        Property.objects.filter(pk=pk).update(inquiries_count=F('inquiries_count') + 1)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_inquiries(request):
    """Agent/owner retrieves all inquiries on their properties."""
    if request.user.role not in ('agent', 'owner'):
        return Response(
            {'detail': 'Only agents and property owners can view inquiries.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    inquiries = Inquiry.objects.filter(property__agent=request.user).prefetch_related('replies')

    property_id = request.GET.get('property')
    if property_id:
        inquiries = inquiries.filter(property_id=property_id)

    unread_only = request.GET.get('unread')
    if unread_only == 'true':
        inquiries = inquiries.filter(is_read=False)

    serializer = InquirySerializer(inquiries, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_inquiry_read(request, pk):
    """Agent/owner marks an inquiry as read."""
    try:
        inquiry = Inquiry.objects.get(pk=pk, property__agent=request.user)
    except Inquiry.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    inquiry.is_read = True
    inquiry.save(update_fields=['is_read'])
    return Response({'detail': 'Marked as read.'})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_inquiry(request, pk):
    """Agent/owner deletes an entire inquiry and its replies."""
    try:
        inquiry = Inquiry.objects.get(pk=pk, property__agent=request.user)
    except Inquiry.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    inquiry.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def inquiry_replies(request, pk):
    """List or create replies for an inquiry owned by the logged-in user."""
    try:
        inquiry = Inquiry.objects.get(pk=pk, property__agent=request.user)
    except Inquiry.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = InquiryReplySerializer(inquiry.replies.all(), many=True)
        return Response(serializer.data)

    serializer = InquiryReplySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(inquiry=inquiry, sender=request.user)
        if not inquiry.is_read:
            inquiry.is_read = True
            inquiry.save(update_fields=['is_read'])
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_inquiry_reply(request, pk, reply_id):
    """Agent/owner deletes a specific reply message."""
    try:
        reply = InquiryReply.objects.get(
            pk=reply_id,
            inquiry__pk=pk,
            inquiry__property__agent=request.user,
        )
    except InquiryReply.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    reply.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── User-facing notification / chat endpoints ─────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_sent_inquiries(request):
    """User retrieves their own sent inquiries with all replies (chat threads)."""
    inquiries = Inquiry.objects.filter(sender=request.user).prefetch_related('replies')
    serializer = InquirySerializer(inquiries, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_unread_count(request):
    """Total unread agent/owner replies on the user's sent inquiries."""
    count = InquiryReply.objects.filter(
        inquiry__sender=request.user,
        is_read=False,
    ).exclude(sender=request.user).count()
    return Response({'unread_count': count})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_inquiry_reply(request, pk):
    """User sends a follow-up message in their own inquiry thread."""
    try:
        inquiry = Inquiry.objects.get(pk=pk, sender=request.user)
    except Inquiry.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = InquiryReplySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(inquiry=inquiry, sender=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def user_mark_inquiry_read(request, pk):
    """User marks all agent/owner replies in their thread as read."""
    try:
        inquiry = Inquiry.objects.get(pk=pk, sender=request.user)
    except Inquiry.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    inquiry.replies.exclude(sender=request.user).filter(is_read=False).update(is_read=True)
    return Response({'detail': 'Marked as read.'})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def user_delete_inquiry(request, pk):
    """User deletes their own inquiry thread entirely."""
    try:
        inquiry = Inquiry.objects.get(pk=pk, sender=request.user)
    except Inquiry.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    inquiry.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def user_delete_reply(request, pk, reply_id):
    """User deletes one of their own reply messages in a thread."""
    try:
        reply = InquiryReply.objects.get(
            pk=reply_id,
            inquiry__pk=pk,
            inquiry__sender=request.user,
            sender=request.user,
        )
    except InquiryReply.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    reply.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Admin endpoints ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_all_properties(request):
    if request.user.role != 'admin':
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
    qs = Property.objects.select_related('agent').order_by('-created_at')
    agent_id = request.query_params.get('agent')
    if agent_id:
        qs = qs.filter(agent_id=agent_id)
    search = request.query_params.get('search', '')
    if search:
        from django.db.models import Q as DQ
        qs = qs.filter(
            DQ(title__icontains=search) |
            DQ(city_state__icontains=search) |
            DQ(address__icontains=search)
        )
    serializer = PropertySerializer(qs, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def admin_delete_property(request, pk):
    if request.user.role != 'admin':
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        prop = Property.objects.get(pk=pk)
    except Property.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    prop.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
