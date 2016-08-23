from django.db import models

from osf_models.models.base import BaseModel, ObjectIDMixin
from osf_models.models.node import AbstractNode

class NodeLink(ObjectIDMixin, BaseModel):
    """A link to a Node. The Pointer delegates all but a few methods to its
    contained Node. Forking and registration are overridden such that the
    link is cloned, but its contained Node is not.
    """
    #: Whether this is a pointer or not
    primary = False

    parent_node = models.ForeignKey(AbstractNode,
                                    related_name='node_links',
                                    on_delete=models.SET_NULL,
                                    null=True, blank=True)

    node = models.ForeignKey('AbstractNode', on_delete=models.SET_NULL, null=True, blank=True)

    def _clone(self):
        if self.node:
            clone = self.clone()
            clone.node = self.node
            clone.save()
            return clone

    def fork_node(self, *args, **kwargs):
        return self._clone()

    def register_node(self, *args, **kwargs):
        return self._clone()

    def use_as_template(self, *args, **kwargs):
        return self._clone()

    def resolve(self):
        return self.node

    def __getattr__(self, item):
        """Delegate attribute access to the node being pointed to."""
        # Prevent backref lookups from being overriden by proxied node
        try:
            return super(NodeLink, self).__getattr__(item)
        except AttributeError:
            pass
        if self.node:
            return getattr(self.node, item)
        raise AttributeError(
            'Pointer object has no attribute {0}'.format(
                item
            )
        )

def get_node_link_parent(node_link):
    """Given a `Pointer` object, return its parent node.
    """
    # The `parent_node` property of the `Pointer` schema refers to the parents
    # of the pointed-at `Node`, not the parents of the `Pointer`; use the
    # back-reference syntax to find the parents of the `Pointer`.
    parent_refs = node_link.parent_node  # TODO: Verify this
    assert len(parent_refs) == 1, 'Pointer must have exactly one parent.'
    return parent_refs[0]

