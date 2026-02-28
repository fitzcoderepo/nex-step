from django.db import models
from accounts.models import Business, User
import uuid


class Flow(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="flows")

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    root_node = models.OneToOneField("Node",on_delete=models.SET_NULL,null=True,blank=True,related_name="root_of_flow",)
    published_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name="published_flows",)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_flows")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.business.name})"


class Node(models.Model):
    class NodeType(models.TextChoices):
        INFO = "info", "Info"
        QUESTION = "question", "Question"
        INSTRUCTION = "instruction", "Instruction"
        RESOLUTION = "resolution", "Resolution"
        ESCALATION = "escalation", "Escalation"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE, related_name="nodes")
    node_type = models.CharField(max_length=15, choices=NodeType.choices, default=NodeType.INFO)
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.node_type} — {self.title or self.id} ({self.flow.name})"

    @property
    def is_terminal(self):
        return self.node_type in [self.NodeType.RESOLUTION, self.NodeType.ESCALATION]

    @property
    def has_options(self):
        return self.options.exists()


class Option(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="options")
    # so deleting a node doesn't cascade delete all options pointing to it. Instead they become detached and can be flagged as broken in editor
    next_node = models.ForeignKey(Node,on_delete=models.SET_NULL,null=True,blank=True,related_name="incoming_options")
    label = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.label} → {self.next_node}"


class NodeMedia(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        FILE = "file", "File"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="media")
    media_type = models.CharField(max_length=10, choices=MediaType.choices)
    file = models.FileField(upload_to="node_media/", null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.media_type} — {self.node}"

    # method to enforce every media item has either a file or url, never both and never neither
    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.file and not self.url:
            raise ValidationError("A media item must have either a file or a URL.")
        if self.file and self.url:
            raise ValidationError("A media item cannot have both a file and a URL.")
