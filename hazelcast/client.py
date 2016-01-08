import logging

from hazelcast.cluster import ClusterService, RandomLoadBalancer
from hazelcast.config import ClientConfig
from hazelcast.connection import ConnectionManager, Heartbeat
from hazelcast.invocation import InvocationService, ListenerService
from hazelcast.partition import PartitionService
from hazelcast.proxy import ProxyManager, MAP_SERVICE, QUEUE_SERVICE
from hazelcast.reactor import AsyncoreReactor
from hazelcast.serialization import SerializationServiceV1


class HazelcastClient(object):
    logger = logging.getLogger("HazelcastClient")
    _config = None

    def __init__(self, config=None):
        self.config = config or ClientConfig()
        self.reactor = AsyncoreReactor()
        self.connection_manager = ConnectionManager(self, self.reactor.new_connection)
        self.heartbeat = Heartbeat(self)
        self.invoker = InvocationService(self)
        self.listener = ListenerService(self)
        self.cluster = ClusterService(config, self)
        self.partition_service = PartitionService(self)
        self.proxy = ProxyManager(self)
        self.load_balancer = RandomLoadBalancer(self.cluster)
        self.serializer = SerializationServiceV1(serialization_config=config.serialization_config)

        self._start()

    def _start(self):
        self.reactor.start()
        try:
            self.cluster.start()
            self.heartbeat.start()
            self.partition_service.start()
        except:
            self.reactor.shutdown()
            raise
        self.logger.info("Client started.")

    def get_map(self, name):
        return self.proxy.get_or_create(MAP_SERVICE, name)

    def get_queue(self, name):
        return self.proxy.get_or_create(QUEUE_SERVICE, name)

    def shutdown(self):
        self.partition_service.shutdown()
        self.heartbeat.shutdown()
        self.cluster.shutdown()
        self.reactor.shutdown()
        self.logger.info("Client shutdown.")


