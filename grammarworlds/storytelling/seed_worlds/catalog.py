"""Auditable coverage of the twenty Luna prose seeds, separate from prototypes."""
from pathlib import Path
import hashlib

SOURCE_ROOT = Path(__file__).resolve().parents[3] / 'storyscenes/design/agents_api_trial_20261024/luna_high_direct_20'
SEED_SCENARIOS = ('bakery','puppets','greenhouse','seaside','library','snow','picnic','music',
                  'market','camp','pottery','orchard','costume','pond','repair','museum',
                  'laundry','trail','festival','biscuit')


def source_record(name):
    number = SEED_SCENARIOS.index(name)+1
    path = SOURCE_ROOT / f'{number:02}_{name}' / 'story.txt'
    return dict(number=number, scenario=name, path=str(path),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())
