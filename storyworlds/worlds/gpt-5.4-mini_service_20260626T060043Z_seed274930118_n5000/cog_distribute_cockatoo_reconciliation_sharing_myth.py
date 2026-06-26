#!/usr/bin/env python3
"""
A small mythic storyworld about a broken cog, a sharing dispute, and a
cockatoo who carries a message toward reconciliation.

The domain is intentionally narrow: a village hall keeps an old chorus machine
made of cogs, a pair of siblings disagree about how to distribute its pieces,
and a cockatoo helps them make peace by sharing the work and the credit.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wears: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    bird: object | None = None
    cog: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str = "the village hall"
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StoryParams:
    setting: str = "hall"
    seed: Optional[int] = None
    CURATED: list = field(default_factory=list)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _rule_tension(world: World) -> list[str]:
    out = []
    child_a = world.entities["Astra"]
    child_b = world.entities["Borin"]
    if child_a.memes.get("wants_share", 0) >= THRESHOLD and child_b.memes.get("wants_share", 0) >= THRESHOLD:
        if child_a.memes.get("tension", 0) < THRESHOLD:
            child_a.memes["tension"] = 1
            child_b.memes["tension"] = 1
            out.append("The hall grew tight as both children reached for the same bright cog.")
    return out


def _rule_reconciliation(world: World) -> list[str]:
    out = []
    a = world.entities["Astra"]
    b = world.entities["Borin"]
    bird = world.entities["Kiki"]
    if a.memes.get("softened", 0) >= THRESHOLD and b.memes.get("softened", 0) >= THRESHOLD:
        sig = ("reconcile",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        a.memes["peace"] = 1
        b.memes["peace"] = 1
        out.append("__reconcile__")
    if bird.memes.get("sharing_message", 0) >= THRESHOLD:
        out.append("__sharing__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_rule_tension, _rule_reconciliation):
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    if s != "__reconcile__" and s != "__sharing__":
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "hall": Setting(place="the village hall", affords={"distribute", "share"}),
}

COGS = {
    "sun_cog": {"label": "sun-bright cog", "phrase": "a sun-bright cog carved with tiny rays"},
    "moon_cog": {"label": "moon-silver cog", "phrase": "a moon-silver cog carved with little crescents"},
    "heart_cog": {"label": "heart-red cog", "phrase": "a heart-red cog that fit the chorus wheel"},
}

NAMES = ["Astra", "Borin", "Kiki"]
TRAITS = ["wise", "curious", "gentle", "proud"]


ASP_RULES = r"""
% Facts from the registries:
% setting(S), affords(S,A), cog(C), bird(B), wants(A,C), shares(B), at_risk(C)

at_risk(C) :- cog(C).
conflict(A,B,C) :- wants(A,C), wants(B,C), A != B, at_risk(C).
can_share(A,B) :- bird(B), shares(B), conflict(A,_,_).
reconcile(A,B) :- conflict(A,B,_), can_share(A,B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid in COGS:
        lines.append(asp.fact("cog", cid))
    lines.append(asp.fact("bird", "Kiki"))
    lines.append(asp.fact("shares", "Kiki"))
    lines.append(asp.fact("wants", "Astra", "sun_cog"))
    lines.append(asp.fact("wants", "Borin", "sun_cog"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("hall", "distribute", "sun_cog"), ("hall", "share", "sun_cog")]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reconcile/2."))
    return sorted(set(asp.atoms(model, "reconcile")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = {("Astra", "Borin")}
    if clingo_set == python_set:
        print("OK: clingo gate matches reconciliation logic.")
        return 0
    print("MISMATCH between clingo and reconciliation logic:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: cogs, sharing, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "setting", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=getattr(args, "setting", None) or "hall", seed=None)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.setting))

    a = world.add(Entity(id="Astra", kind="character", type="girl", label="Astra"))
    b = world.add(Entity(id="Borin", kind="character", type="boy", label="Borin"))
    bird = world.add(Entity(id="Kiki", kind="character", type="bird", label="Kiki", plural=False))
    cog = world.add(Entity(id="sun_cog", type="cog", label="sun-bright cog", phrase=COGS["sun_cog"]["phrase"], owner=None))
    world.add(Entity(id="moon_cog", type="cog", label="moon-silver cog", phrase=COGS["moon_cog"]["phrase"]))
    world.add(Entity(id="heart_cog", type="cog", label="heart-red cog", phrase=COGS["heart_cog"]["phrase"]))

    a.memes["love_machine"] = 1
    b.memes["love_machine"] = 1
    bird.memes["sharing_message"] = 1
    a.memes["wants_share"] = 1
    b.memes["wants_share"] = 1

    world.say(
        f"In the old village hall, Astra and Borin guarded the chorus wheel, "
        f"which shone around {cog.label} like a tiny sun."
    )
    world.say(
        "Each child wanted the shining cog for their own song, and neither would let go."
    )
    world.para()
    world.say(
        f"Then Kiki the cockatoo fluttered down from the rafters and cried, "
        f"\"Do not distribute the gift as if it were a stone; share it like bread.\""
    )
    world.say(
        "The words stilled the quarrel, because the cockatoo spoke with an old and trusted voice."
    )

    propagate(world, narrate=False)
    world.para()

    a.memes["softened"] = 1
    b.memes["softened"] = 1
    world.say(
        "Astra lowered her hands and remembered the wheel had been made for both of them."
    )
    world.say(
        "Borin nodded and said the work could be shared, and the glory could be shared too."
    )
    world.say(
        "So they placed the cog back into the chorus wheel together, one guiding and one steadying."
    )
    world.say(
        "When the handle turned, the hall filled with a clear song, and the cockatoo bowed as if the sky itself had answered."
    )
    world.say(
        "That night the children sat side by side, no longer rivals, listening to the wheel hum in peace."
    )

    world.facts.update(
        a=a, b=b, bird=bird, cog=cog, setting=params.setting,
        reconciliation=True, sharing=True
    )

    story_qa = [
        QAItem(
            question="Who helped Astra and Borin make peace?",
            answer="Kiki the cockatoo helped them make peace by speaking the old warning and urging them to share.",
        ),
        QAItem(
            question="What did Astra and Borin learn to do with the cog?",
            answer="They learned to share the cog and the work of returning it to the chorus wheel.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="The quarrel ended, the cog went back into the wheel, and the village hall filled with music instead of argument.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a cog?",
            answer="A cog is a toothed wheel that turns and helps a machine move.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting more than one person use, hold, or enjoy something fairly.",
        ),
        QAItem(
            question="What is a cockatoo?",
            answer="A cockatoo is a bird with a curved beak and a lively crest, and it can be a noisy companion.",
        ),
    ]

    prompts = [
        'Write a short myth about a cog that two children both want to distribute, until a cockatoo teaches reconciliation.',
        'Tell a gentle mythic story in which sharing solves a quarrel over a bright cog.',
        'Write a child-friendly legend about a cockatoo who helps two children repair a village hall chorus wheel.',
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [StoryParams(setting="hall")]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reconcile/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show reconcile/2."))
        print(f"{len(set(asp.atoms(model, 'reconcile')))} reconciliation pair(s):")
        for a, b in sorted(set(asp.atoms(model, "reconcile"))):
            print(f"  {a} with {b}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
