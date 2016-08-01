from django.db import models
from osf_models.models.base import BaseModel, BSONGuidMixin


class AlternativeCitation(BSONGuidMixin, BaseModel):
    name = models.CharField(max_length=256)
    text = models.CharField(max_length=2048)

    def to_json(self):
        return {
            'id': self._id,
            'name': self.name,
            'text': self.text
        }
