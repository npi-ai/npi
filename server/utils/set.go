package utils

// Set represents a generic set
type Set[T comparable] map[T]struct{}

// NewSet creates a new set
func NewSet[T comparable]() Set[T] {
	return make(Set[T])
}

// Add adds an element to the set
func (s Set[T]) Add(element T) {
	s[element] = struct{}{}
}

// Remove removes an element from the set
func (s Set[T]) Remove(element T) {
	delete(s, element)
}

// Contains checks if an element is in the set
func (s Set[T]) Contains(element T) bool {
	_, exists := s[element]
	return exists
}

// Union returns the union of two sets
func Union[T comparable](set1, set2 Set[T]) Set[T] {
	result := NewSet[T]()
	for key := range set1 {
		result[key] = struct{}{}
	}
	for key := range set2 {
		result[key] = struct{}{}
	}
	return result
}

// Intersection returns the intersection of two sets
func Intersection[T comparable](set1, set2 Set[T]) Set[T] {
	result := NewSet[T]()
	for key := range set1 {
		if _, exists := set2[key]; exists {
			result[key] = struct{}{}
		}
	}
	return result
}

// Difference returns the difference of two sets (set1 - set2)
func Difference[T comparable](set1, set2 Set[T]) Set[T] {
	result := NewSet[T]()
	for key := range set1 {
		if _, exists := set2[key]; !exists {
			result[key] = struct{}{}
		}
	}
	return result
}
