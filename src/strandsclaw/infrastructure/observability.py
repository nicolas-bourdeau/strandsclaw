from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from typing import Callable


@dataclass
class RuntimeEventLogger:
    sink: Callable[[str], None] | None = None

    def emit(self, event: str, **fields: Any) -> None:
        payload = {
            "timestamp": datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "event": event,
            **fields,
        }
        serialized = json.dumps(payload, sort_keys=True)
        if self.sink is not None:
            self.sink(serialized)
