# Class used to make a buffer of data to dump
# to the SD Card every 20 seconds.
class CircularQueue:

    def __init__(self, capacity):
        self.capacity = capacity
        self.queue = [None] * capacity
        self.tail = -1
        self.head = 0
        self.size = 0

    # Add a value to the queue
    def enqueue(self, item):

        if self.size == self.capacity:
            print("Error: Queue is Full")

        else:
            self.tail = (self.tail + 1) % self.capacity
            self.queue[self.tail] = item
            self.size = self.size + 1

    # Remove a value from the queue
    def dequeue(self):
        if self.size == 0:
            #print("Error: Queue is Empty")
            return

        else:
            tmp = self.queue[self.head]
            self.head = (self.head + 1) % self.capacity

        self.size = self.size - 1
        return tmp

    # Check the value at the head of the queue
    def peek(self):
        tmp = self.queue[self.head]
        return tmp

    # Check if the queue is full
    def is_full(self):
        if self.size == self.capacity:
            return True
        else:
            return False

    # Check if the queue is empty
    def is_empty(self):
        if self.size == 0:
            return True
        else:
            return False

    # Print the entire queue
    def display(self):

        if self.size == 0:
            print("Queue is Empty \n")

        else:
            index = self.head

            for i in range(self.size):
                print(self.queue[index])
                index = (index + 1) % self.capacity

    # Clear the entire queue
    def clear_queue(self):
        self.queue = [None] * self.capacity
        self.size = 0

    # Used for peak detect to access the queue array
    def show_queue_list(self):
        return self.queue
