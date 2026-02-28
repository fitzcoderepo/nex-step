from rest_framework import serializers
from flows.models import Node, NodeMedia


class NodeMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeMedia
        fields = [
            'id',
            'media_type',
            'file',
            'url',
            'caption',
            'order',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        file = data.get('file')
        url = data.get('url')

        if not file and not url:
            raise serializers.ValidationError('A media item must have either a file or a URL.')
        
        if file and url:
            raise serializers.ValidationError('A media item cannot have both a file and a URL.')
        
        return data


class NodeSerializer(serializers.ModelSerializer):
    media = NodeMediaSerializer(many=True, read_only=True)
    is_terminal = serializers.BooleanField(read_only=True)
    has_options = serializers.BooleanField(read_only=True)

    class Meta:
        model = Node
        fields = [
            'id',
            'flow',
            'node_type',
            'title',
            'content',
            'order',
            'is_terminal',
            'has_options',
            'media',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'flow', 'created_at', 'updated_at']


class NodeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = [
            'node_type',
            'title',
            'content',
            'order',
        ]

    def validate_node_type(self, value):
        return value

    def create(self, validated_data):
        flow = self.context['flow']
        
        return Node.objects.create(flow=flow, **validated_data)


class NodeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = [
            'node_type',
            'title',
            'content',
            'order',
        ]

# lightweight version to return just enough info for the visual tree editor to render the canvas without fetching full content and media for every node
class NodeSummarySerializer(serializers.ModelSerializer):
    is_terminal = serializers.BooleanField(read_only=True)
    has_options = serializers.BooleanField(read_only=True)

    class Meta:
        model = Node
        fields = [
            'id',
            'node_type',
            'title',
            'order',
            'is_terminal',
            'has_options',
        ]