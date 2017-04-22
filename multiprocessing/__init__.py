################################################################################
# base.multiprocessing.__init__
#
# Copyright 2017. Djamel Grine.
#
# Redistribution and use in source and binary forms, with or without 
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, 
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, 
#    this list of conditions and the following disclaimer in the documentation 
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.
################################################################################
from base.application.log import get_logger
from Queue import Empty
from multiprocessing import Process, JoinableQueue, Queue, current_process

log = get_logger()

# Standard queues
InputQueue = JoinableQueue
OutputQueue = Queue

def drain_queue(queue):
    """
    Empties a queue into a list.
    """
    collection = []
    while True:
        try:
            item = queue.get(1, 1)
            collection.append(item)

        except Empty as error:
            break
    return collection

class Action(dict): pass

class WorkerBase(Process):
    """
    Base class for any multiprocessing worker.
    """

    class ExceptionBehavior:
        """
        Enum class holding exception behavior control constants.
        """
        SKIP = 0
        RETRY = 1
        PROPAGATE = 2

    def __init__(self, qin, qout):
        super(WorkerBase, self).__init__()
        self.qin = qin
        self.qout = qout

    def run(self):
        try:
            log.noise("Worker status: %s", current_process())
            if not hasattr(self, 'initialized'):
                self.setup()
                setattr(self, 'initialized', True)

            while True:
                # Fetch the next item
                try:
                    item = self.get()

                except Empty as error:
                    # Nothing more to process
                    break

                # Process the item
                result = self.process_dispatch(item) if item is not None else None

                # Save the result
                if result is not None: self.put(result)

                # We're done with this item
                self.qin.task_done()

        except Exception as error:
            # Something unexpectedly went wrong, log and bail out
            log.exception(error)

    def setup(self):
        """
        Initializes the state of the object in the new process.
        """
        pass

    def get(self):
        """
        Retrieves an item from the input queue.
        """
        return self.qin.get(1, 1)

    def put(self, result):
        """
        Stores the result in the output queue.
        """
        self.qout.put(result, 1, 1)

    def process_dispatch(self, item):
        try:
            if Action == type(item):
                action = item['action']
                params = item['params'] if 'params' in item else {}

                # Call the callback function that handles this action
                cbfunc = 'action_%s' % action
                if not hasattr(self, cbfunc): return
                return getattr(self, cbfunc)(params)

            else:
                return self.process(item)

        except Exception as error:
            # Ask the exception handler what to do
            exception_behavior = self.handle_error(error, item)
            if self.ExceptionBehavior.SKIP == exception_behavior:
                return
            elif self.ExceptionBehavior.RETRY == exception_behavior:
                return self.process_dispatch(item)
            elif self.ExceptionBehavior.PROPAGATE == exception_behavior:
                raise
            else:
                raise

    def handle_error(self, error, item):
        return self.ExceptionBehavior.PROPAGATE

    def process(self, item):
        raise NotImplementedError()

class DatabaseWorkerBase(WorkerBase):
    """
    Worker that operates on a database.
    It has support for batch loading through 'actions'.
    """

    Action = Action

    # Default load action: start at id 1 and load a 1000 items
    LOAD_ACTION = Action(
        {
            'action': 'load',
            'params': {'offset': 1, 'limit': 1000}
        }
   )

    @property
    def db(self):
        raise NotImplementedError()

    def query_load(self, offset, limit):
        """
        Generates the query for retrieval of database records.
        """
        assert hasattr(self, 'table'), "Missing 'table' attribute"
        query = "SELECT * FROM %s "\
                "WHERE %s >= %d "\
                "ORDER BY %s ASC "\
                "LIMIT %d" % \
                    (
                        self.table,
                        self.id_load,
                        offset,
                        self.id_load,
                        limit
                   )
        return query

    @property
    def id_load(self):
        return "id"

    def action_load(self, params):
        log.noise("Loading next batch: %s", params)

        # Extract the action parameters
        offset = params['offset'] 
        limit = params['limit']

        # Fetch the next batch
        cursor = self.db.cursor()
        cursor.execute(self.query_load(**params))
        raw_records = cursor.fetchall()
        count = len(raw_records)
        if 0 != count:
            # Transform the raw record into a dict record
            columns = [i[0] for i in cursor.description]
            records = [dict(zip(columns, raw_record)) for raw_record in raw_records]

            # Add the records to the queue
            for record in records:
                # log.noise("Adding record id=%d", record[self.id_load])
                self.qin.put(record)

            # Adjust the offset
            offset = records[-1][self.id_load] + 1

            # Add an action to retrieve the next batch
            self.qin.put(
                Action(
                    {
                        'action': 'load',
                        'params': {'offset': offset, 'limit': limit}
                    }
               )
           )
            log.noise("Loading of batch completed: %d records retrieved.", count)
        else:
            # No more records
            log.noise("Finished loading all records.")
        cursor.close()

    def process(self, record):
        raise NotImplementedError()

