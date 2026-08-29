from dataclasses import dataclass
@dataclass(frozen=True)
class Observation:
    observation_id:int; produced_timestamp:float; payload:float
@dataclass(frozen=True)
class ActionChunk:
    source_observation_id:int; source_observation_timestamp:float; policy_start_timestamp:float; policy_end_timestamp:float; actions:tuple[float,...]
@dataclass(frozen=True)
class ExecutionRecord:
    source_observation_id:int; source_observation_timestamp:float; policy_start_timestamp:float; policy_end_timestamp:float; action_chunk_index:int; action_index_in_chunk:int; action_value:float; execution_timestamp:float
    @property
    def policy_latency_ms(self): return (self.policy_end_timestamp-self.policy_start_timestamp)*1000
    @property
    def action_age_ms(self): return (self.execution_timestamp-self.source_observation_timestamp)*1000
