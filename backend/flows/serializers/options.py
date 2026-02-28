from rest_framework import serializers
from flows.models import Option, Node


class OptionSerializer(serializers.ModelSerializer):
    next_node_title = serializers.SerializerMethodField()

    class Meta:
        model = Option
        fields = [
            'id',
            'node',
            'next_node',
            'next_node_title',
            'label',
            'order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'node', 'created_at', 'updated_at']

    # computed field that returns title of node to allow authors to see at a glance where each option leads without having to look up the node separately
    def get_next_node_title(self, obj):
        if obj.next_node:
            return obj.next_node.title or str(obj.next_node.id)
        
        return None


class OptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = [
            'next_node',
            'label',
            'order',
        ]
    # Make sure the next node belongs to the same flow to prevent cross-flow connections. Prevent an option from pointing back to its own node to avoid infinite loop
    def validate_next_node(self, value):
        if value is None:
            
            return value

        node = self.context['node']

        if value == node:
            raise serializers.ValidationError('An option cannot point back to its own node.')

        if value.flow != node.flow:
            raise serializers.ValidationError('The next node must belong to the same flow.' )

        return value
    
    # Prevents adding options to terminal nodes since they're meant to end a flow
    def validate(self, data):
        node = self.context['node']

        if node.is_terminal:
            raise serializers.ValidationError('Terminal nodes (resolution, escalation) cannot have options.')

        return data

    def create(self, validated_data):
        node = self.context['node']
        
        return Option.objects.create(node=node, **validated_data)


class OptionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = [
            'next_node',
            'label',
            'order',
        ]

    def validate_next_node(self, value):
        if value is None:
            return value

        node = self.instance.node

        if value == node:
            raise serializers.ValidationError('An option cannot point back to its own node.')

        if value.flow != node.flow:
            raise serializers.ValidationError('The next node must belong to the same flow.')

        return value