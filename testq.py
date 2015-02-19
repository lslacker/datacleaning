import Queue
import threading

# input queue to be processed by many threads
q_in = Queue.Queue(maxsize=0)

# output queue to be processed by one thread
q_out = Queue.Queue(maxsize=0)

# number of worker threads to complete the processing
num_worker_threads = 10

# process that each worker thread will execute until the Queue is empty
def worker():
    while True:
        # get item from queue, do work on it, let queue know processing is done for one item
        item = q_in.get()
        q_out.put(do_work(item))
        q_in.task_done()

# squares a number and returns the number and its square
def do_work(item):
    return (item,item*item)

# another queued thread we will use to print output
def printer():
    while True:
        # get an item processed by worker threads and print the result. Let queue know item has been processed
        item = q_out.get()
        print "%d squared is : %d" % item
        q_out.task_done()

# launch all of our queued processes
def main():
    # Launches a number of worker threads to perform operations using the queue of inputs
    for i in range(num_worker_threads):
         t = threading.Thread(target=worker)
         t.daemon = True
         t.start()

    # launches a single "printer" thread to output the result (makes things neater)
    t = threading.Thread(target=printer)
    t.daemon = True
    t.start()

    # put items on the input queue (numbers to be squared)
    for item in range(10):
        q_in.put(item)

    # wait for two queues to be emptied (and workers to close)   
    q_in.join()       # block until all tasks are done
    q_out.join()

    print "Processing Complete"

main()