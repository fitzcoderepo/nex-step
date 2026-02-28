from rest_framework import serializers
from flows.models import Flow

# read only, used for display, widget facing
class FlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flow
        fields = [
            'id',
            'business',
            'name',
            'description',
            'status',
            'root_node',
            'published_by',
            'published_at',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


# lightweight flow summary
class FlowSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Flow
        fields = [
            'id',
            'name',
            'status',
            'created_at',
        ]
        read_only_fields = fields



# flow creation
class FlowCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flow
        fields = [
            'name',
            'description',
        ]

    def create(self, validated_data):
        business = self.context['request'].user.business
        created_by = self.context['request'].user
        
        return Flow.objects.create(business=business,created_by=created_by,status=Flow.Status.DRAFT, **validated_data)
    

# flow updating
class FlowUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flow
        fields = [
            'name',
            'description',
            'root_node',
        ]

    def validate(self, data):
        if self.instance.status == Flow.Status.PUBLISHED:
            raise serializers.ValidationError('You must unpublish a flow to edit.')
        
        return data
        
      
# flow publishing
class FlowPublishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flow
        fields = [
            'status'
        ]

    def validate(self, data):
        requesting_user = self.context['request'].user

        if not requesting_user.can_publish:
            raise serializers.ValidationError('You must be an Admin or Owner to publish.')
        
        if self.instance.root_node is None:
            raise serializers.ValidationError('A root node must be set before publishing.')

        return data
    
    def update(self, instance, validated_data):
        from django.utils import timezone

        instance.status = Flow.Status.PUBLISHED
        instance.published_by = self.context['request'].user
        instance.published_at = timezone.now()
        instance.save()

        return instance
        