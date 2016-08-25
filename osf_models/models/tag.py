from django.db import models

from .base import BaseModel

# TODO DELETE ME POST MIGRATION
from modularodm import Q as MQ
# /TODO DELETE ME POST MIGRATION


class Tag(BaseModel):
    # TODO DELETE ME POST MIGRATION
    modm_model_path = 'website.project.model.Tag'
    modm_queryset = None
    # /TODO DELETE ME POST MIGRATION
    name = models.CharField(db_index=True, max_length=1024)
    system = models.BooleanField(default=False)

    def __unicode__(self):
        if self.system:
            return 'System Tag: {}'.format(self.name)
        return u'{}'.format(self.name)

    @classmethod
    def load(cls, data):
        """For compatibility with v1: the tag name used to be the _id,
        so we make Tag.load('tagname') work as if `name` were the primary key.
        """
        try:
            return cls.objects.get(name=data)
        except cls.DoesNotExist:
            return None

    class Meta:
        unique_together = ('name', 'system')
