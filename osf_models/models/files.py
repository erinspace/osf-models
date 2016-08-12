from django.db import models
from osf_models.models.base import BaseModel
from osf_models.models.base import ObjectIDMixin
from osf_models.models.comment import CommentableMixin
from osf_models.utils.base import api_v2_url
from osf_models.utils.datetime_aware_jsonfield import DateTimeAwareJSONField

from website.files.models import FileNode


class StoredFileNode(CommentableMixin, ObjectIDMixin, BaseModel):
    """
        The storage backend for FileNode objects.
        This class should generally not be used or created manually as FileNode
        contains all the helpers required.
        A FileNode wraps a StoredFileNode to provider usable abstraction layer
    """

    # The last time the touch method was called on this FileNode
    last_touched = models.DateTimeField()
    # A list of dictionaries sorted by the 'modified' key
    # The raw output of the metadata request deduped by etag
    # Add regardless it can be pinned to a version or not
    history = DateTimeAwareJSONField()
    # A concrete version of a FileNode, must have an identifier
    versions = models.ManyToManyField('FileVersion')

    node = models.ForeignKey('Node', blank=False, null=False)
    parent = models.ForeignKey('StoredFileNode', blank=True, null=True, default=None, related_name='child')
    copied_from = models.ForeignKey('StoredFileNode', blank=True, null=True, default=None, related_name='copy_of')

    is_file = models.BooleanField(default=True)
    provider = models.CharField(blank=False, null=False)

    name = models.CharField(blank=False, null=False)
    path = models.CharField(blank=False, null=False)
    materialized_path = models.CharField(blank=False, null=False)

    # The User that has this file "checked out"
    # Should only be used for OsfStorage
    checkout = models.ForeignKey('OSFUser', blank=True, null=True)

    # Tags for a file, currently only used for osfStorage
    tags = models.ManyToManyField('Tag')

    @property
    def deep_url(self):
        return self.wrapped().deep_url

    @property
    def absolute_api_v2_url(self):
        path = '/files/{}/'.format(self._id)
        return api_v2_url(path)

    # For Comment API compatibility
    @property
    def target_type(self):
        """The object "type" used in the OSF v2 API."""
        return 'files'

    @property
    def root_target_page(self):
        """The comment page type associated with StoredFileNodes."""
        return 'files'

    @property
    def is_deleted(self):
        if self.provider == 'osfstorage':
            return False

    def belongs_to_node(self, node_id):
        """Check whether the file is attached to the specified node."""
        return self.node._id == node_id

    def get_extra_log_params(self, comment):
        return {'file': {'name': self.name, 'url': comment.get_comment_page_url()}}

    # used by django and DRF
    def get_absolute_url(self):
        return self.absolute_api_v2_url

    def wrapped(self):
        """Wrap self in a FileNode subclass
        """
        return FileNode.resolve_class(self.provider, int(self.is_file))(self)

    def get_guid(self, create=False):
        """Attempt to find a Guid that points to this object.
        One will be created if requested.

        :param Boolean create: Should we generate a GUID if there isn't one?  Default: False
        :rtype: Guid or None
        """
        # TODO WAT, relational solution?
        try:
            # Note sometimes multiple GUIDs can exist for
            # a single object. Just go with the first one
            return Guid.find(Q('referent', 'eq', self))[0]
        except IndexError:
            if not create:
                return None
        return Guid.generate(self)

    class Meta:
        unique_together = [
            ('node', 'name', 'parent', 'is_file', 'provider', 'path',)
        ]
        index_together = [
            ('path', 'node', 'is_file', 'provider'),
            ('node', 'is_file', 'provider'),
        ]
