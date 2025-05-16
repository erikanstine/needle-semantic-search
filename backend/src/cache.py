from typing import Any, Dict, Optional


class Node:
    def __init__(self, key=None, val=None):
        self.left: Optional[Node] = None
        self.right: Optional[Node] = None
        self.key = key
        self.value = val


# Implementing my own LRUCache because it's fun!
# head is recent
class LRUCache:
    def __init__(self, capacity=50):
        self.capacity: int = capacity
        self.map: Dict[Any, Node] = {}
        self.head, self.tail = Node(), Node()
        self.head.right = self.tail
        self.tail.left = self.head

    def _add(self, k: Any, v: Any):
        tmp: Node = self.head.right
        node = Node(k, v)
        self.head.right = node
        node.left = self.head
        node.right = tmp
        tmp.left = node
        self.map[k] = node

    def _delete(self, n: Node):
        n.left.right = n.right
        n.right.left = n.left
        del self.map[n.key]

    def get(self, k: Any) -> Optional[Any]:
        if self.map.get(k):
            n = self.map[k]
            self._delete(n)
            self._add(n.key, n.value)
            return self.map[k].value
        return

    def set(self, k: Any, v: Any):
        if len(self.map) >= self.capacity:
            self._delete(self.tail.left)
        if self.map.get(k):
            self._delete(self.map[k])
        self._add(k, v)
