import time
CACHE_TTL = 5 * 60 * 1000

class CacheEntry:
	def __init__(self, data):
		self.data = data
		self.timestamp = time.time()

class SimpleCache:
	def __init__(self):
		self.cache = {}

	def get(self, key):
		entry = self.cache.get(key)
		if not entry:
			return None
		if time.time() - entry.timestamp > CACHE_TTL:
			self.delete(key)
			return None
		return entry.data

	def set(self, key, value):
		self.cache[key] = CacheEntry(value)

	def delete(self, key):
		if key in self.cache:
			del self.cache[key]

	def clean_up(self):
		now = time.time()
		keys_to_delete = [key for key, entry in self.cache.items() if now - entry.timestamp > CACHE_TTL]
		for key in keys_to_delete:
			self.delete(key)
