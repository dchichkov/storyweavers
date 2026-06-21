#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cozy_rejection_suspense_conflict_fable.py
=========================================================================

A small, self-contained storyworld in a fable style: a cozy shelter is offered,
a proud request is refused, suspense rises, conflict follows, and the ending
proves what changed.

The domain is a woodland led by a patient badger, a careful mouse, and a fox
who wants to borrow a lantern for a moonlit walk. The story stays tight and
state-driven: a refusal creates tension, a dangerous pause makes the night feel
uncertain, and a wise turn resolves the conflict into a safer, warmer ending.

The script follows the shared Storyweavers contract:
- typed entities with meters and memes
- a Python reasonableness gate plus inline ASP twin
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- three Q&A sets grounded in world state
- --verify smoke-tests normal generation and checks ASP parity
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

COZY_MIN = 1.0
SUSPENSE_MIN = 1.0

WOODLAND_TRAITS = {"patient", "careful", "wise"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    shelter: str
    dark_place: str
    shelter_image: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    type: str
    label: str
    trait: str
    role: str
    tags: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    safe: bool
    warm: bool
    gives_light: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Want:
    id: str
    ask: str
    reason: str
    risk: str
    success: str
    refusal: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = {k: v for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    seeker: str
    seeker_type: str
    seeker_trait: str
    guardian: str
    guardian_type: str
    guardian_trait: str
    want: str
    object: str
    response: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        place="the meadow by the hill",
        shelter="a hollow log",
        dark_place="the hollow log",
        shelter_image="a hollow log with a knitted blanket tucked over the opening",
        mood="soft and quiet",
        tags={"meadow", "cozy", "suspense"},
    ),
    "brook": Setting(
        id="brook",
        place="the brook under the willow",
        shelter="a little den of reeds",
        dark_place="the den of reeds",
        shelter_image="a little den of reeds with a lantern glow inside",
        mood="cool and still",
        tags={"brook", "cozy", "suspense"},
    ),
}

CREATURES = {
    "mouse": Creature("mouse", "mouse", "mouse", "quick and tiny", "seeker", {"mouse"}),
    "fox": Creature("fox", "fox", "fox", "bright and proud", "seeker", {"fox"}),
    "rabbit": Creature("rabbit", "rabbit", "rabbit", "gentle and shy", "guardian", {"rabbit"}),
    "badger": Creature("badger", "badger", "badger", "patient and wise", "guardian", {"badger"}),
}

OBJECTS = {
    "lantern": ObjectThing(
        id="lantern",
        label="lantern",
        phrase="a small lantern with a warm yellow glow",
        safe=True,
        warm=True,
        gives_light=True,
        tags={"lantern", "cozy", "light"},
    ),
    "blanket": ObjectThing(
        id="blanket",
        label="blanket",
        phrase="a wool blanket",
        safe=True,
        warm=True,
        gives_light=False,
        tags={"blanket", "cozy"},
    ),
    "candle": ObjectThing(
        id="candle",
        label="candle",
        phrase="a candle",
        safe=False,
        warm=False,
        gives_light=True,
        tags={"candle", "light"},
    ),
}

WANTS = {
    "borrow_light": Want(
        id="borrow_light",
        ask="borrow the lantern",
        reason="to see the path through the dark",
        risk="it could be dropped in the reeds",
        success="used the lantern only with permission",
        refusal="the lantern stayed where it belonged",
        tags={"borrow", "light", "rejection"},
    ),
    "cross_water": Want(
        id="cross_water",
        ask="cross the brook alone",
        reason="to reach the other side before dawn",
        risk="the reeds could hide a slip",
        success="crossed safely with help",
        refusal="waited for help instead",
        tags={"brook", "risk", "suspense"},
    ),
}

RESPONSES = {
    "gentle_no": {"sense": 3, "kind": "wise", "text": "said no kindly and offered a better choice"},
    "wait": {"sense": 2, "kind": "wise", "text": "asked for patience and a smaller plan"},
    "snatch": {"sense": 1, "kind": "rash", "text": "snatched the lantern away and made the night worse"},
}

SAFE_RESPONSES = {"gentle_no", "wait"}

NAMES = {
    "mouse": ["Mina", "Nip", "Pip", "Tilly"],
    "fox": ["Ren", "Fenn", "Rowan", "Crispin"],
    "rabbit": ["June", "Lara", "Bram", "Willow"],
    "badger": ["Moss", "Alder", "Brindle", "Hearth"],
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for seeker in ["mouse", "fox"]:
            for want in WANTS:
                for obj in OBJECTS:
                    if seek_reasonable(seeker, want, obj):
                        combos.append((setting, seeker, want, obj))
    return combos


def seek_reasonable(seeker: str, want: str, obj: str) -> bool:
    if want == "borrow_light":
        return obj == "lantern" and OBJECTS[obj].safe
    if want == "cross_water":
        return obj in {"blanket", "lantern"} and OBJECTS[obj].safe
    return False


def outcome_of(params: StoryParams) -> str:
    if params.response not in SAFE_RESPONSES:
        return "conflict"
    if params.want == "borrow_light":
        return "cozy"
    return "resolved"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy fable about rejection, suspense, and conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--seeker", choices=["mouse", "fox"])
    ap.add_argument("--want", choices=WANTS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.response and RESPONSES[args.response]["sense"] < 2:
        raise StoryError("(No story: that response is too rash for a fable about wise rejection.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.seeker is None or c[1] == args.seeker)
              and (args.want is None or c[2] == args.want)
              and (args.object is None or c[3] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, seeker, want, obj = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(SAFE_RESPONSES))
    return StoryParams(
        setting=setting,
        seeker=seeker,
        seeker_type=CREATURES[seeker].type,
        seeker_trait=CREATURES[seeker].trait,
        guardian="badger",
        guardian_type="badger",
        guardian_trait=CREATURES["badger"].trait,
        want=want,
        object=obj,
        response=response,
    )


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in ["mouse", "fox"]:
        lines.append(asp.fact("seeker", cid))
    for wid in WANTS:
        lines.append(asp.fact("want", wid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.safe:
            lines.append(asp.fact("safe", oid))
        if obj.gives_light:
            lines.append(asp.fact("light", oid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp["sense"]))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(S,W,O) :- seeker(S), want(W), object(O), seek_ok(W,O).
safe_response(R) :- response(R), sense(R,S), sense_min(M), S >= M.
outcome(cozy) :- safe_response(R), response(R), R != snatch.
outcome(conflict) :- response(snatch).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show safe_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "safe_response"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set((s, se, w, o)[:3] for s, se, w, o in valid_combos()):
        print("MISMATCH: ASP and Python reasonableness differ.")
        rc = 1
    if set(asp_sensible()) != set(SAFE_RESPONSES):
        print("MISMATCH: ASP and Python safe responses differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, seeker=None, want=None, object=None, response=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def _role_name(seeker: Entity) -> str:
    return "little mouse" if seeker.type == "mouse" else "little fox"


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def tell(world: World, params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    seeker_cfg = CREATURES[params.seeker]
    guardian_cfg = CREATURES[params.guardian]
    want = WANTS[params.want]
    obj = OBJECTS[params.object]
    resp = RESPONSES[params.response]

    seeker = world.add(Entity(
        id=params.seeker,
        kind="character",
        type=seeker_cfg.type,
        label=seeker_cfg.label,
        role="seeker",
        traits=[params.seeker_trait],
        tags=set(seeker_cfg.tags),
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type=guardian_cfg.type,
        label=guardian_cfg.label,
        role="guardian",
        traits=[params.guardian_trait],
        tags=set(guardian_cfg.tags),
    ))
    lantern = world.add(Entity(
        id=obj.id,
        kind="thing",
        type=obj.id,
        label=obj.label,
        role="object",
        tags=set(obj.tags),
    ))

    seeker.memes["hope"] += 1
    guardian.memes["calm"] += 1
    world.facts.update(setting=setting, seeker=seeker, guardian=guardian, want=want, obj=obj, resp=resp)

    world.say(
        f"In {setting.place}, {seeker.id} the {_role_name(seeker)} found {setting.shelter_image}. "
        f"It looked cozy enough to keep a secret."
    )
    world.say(
        f"{seeker.id} wanted to {want.ask} {want.reason}, and {guardian.id} watched with kind, careful eyes."
    )
    world.para()
    world.say(
        f"Then {seeker.id} made a request. \"May I {want.ask}?\" "
        f"{guardian.id} felt the question like a pebble in the dark."
    )
    if resp["kind"] == "rash":
        raise StoryError("Rash responses are not allowed in this world; the tale needs a wise refusal.")
    seeker.memes["rejected"] += 1
    seeker.memes["conflict"] += 1
    guardian.memes["boundary"] += 1
    world.say(
        f'\"{want.refusal},\" said {guardian.id}. {guardian.id} {resp["text"]}. '
        f'That answer was a rejection, but not a cruel one.'
    )
    world.say(
        f"Outside, the reeds rustled. {seeker.id} stood very still and listened, as if the night itself might answer."
    )
    world.para()
    seeker.memes["suspense"] += 1
    if params.want == "borrow_light":
        world.say(
            f"{seeker.id} looked at the lantern and then at the dark path. The pause felt long enough to hold a breath."
        )
        world.say(
            f"At last {guardian.id} lowered the lantern to the moss and said, \"If you need light, we can go together.\""
        )
        seeker.memes["relief"] += 1
        guardian.memes["trust"] += 1
        world.say(
            f"So they walked side by side, and the lantern made one small gold pool on the ground while the rest of the night stayed quiet."
        )
        world.say(
            f"In that cozy circle of light, {seeker.id} learned that a boundary can keep a friendship safe."
        )
        setting_img = "the lantern's warm circle on the moss"
    else:
        seeker.memes["worry"] += 1
        world.say(
            f"{seeker.id} wanted to cross at once, but {guardian.id} refused the lonely plan and laid a blanket across the narrow stones as a safer step."
        )
        world.say(
            f"The wind waited, the water whispered, and the two of them crossed together without rushing."
        )
        setting_img = "the blanket laid across the stones"

    world.say(
        f"By dawn, {setting.place} was not less dark, but it was less lonely. The small {setting_img} proved that a wise no can make room for a kinder yes."
    )

    world.facts.update(outcome=outcome_of(params))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a cozy fable that includes the words "cozy" and "rejection".',
        f"Tell a woodland story where {f['seeker'].id} asks to {f['want'].ask}, gets a gentle rejection, and then learns a wiser way.",
        f"Write a suspenseful conflict story for children where a careful guardian says no, but the ending feels warm and kind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker = f["seeker"]
    guardian = f["guardian"]
    want = f["want"]
    qa = [
        QAItem(
            question="Who wanted something in the story?",
            answer=f"{seeker.id} wanted to {want.ask}. The wish came from a need to see the path, but it had to be answered carefully.",
        ),
        QAItem(
            question="Why did the guardian say no?",
            answer=f"{guardian.id} said no because the request would have crossed a boundary and left the night less safe. The rejection protected the little creature from a risky choice.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended warmly, with the two of them choosing a safer way together. The rejection did not break the bond; it helped turn the conflict into trust.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    obj = f["obj"]
    if obj.id == "lantern":
        return [
            QAItem(
                question="What does a lantern do?",
                answer="A lantern gives off a steady light. It helps creatures see in the dark without needing to rush or stumble.",
            ),
            QAItem(
                question="Why can a cozy light make a dark place feel better?",
                answer="A cozy light makes the shadows feel smaller and less strange. It helps everyone stay calm while they move carefully.",
            ),
        ]
    return [
        QAItem(
            question="Why should a small creature wait before crossing water alone?",
            answer="Waiting keeps the creature from slipping into danger. A safer helper can make the crossing steadier and kinder.",
        )
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="meadow", seeker="mouse", seeker_type="mouse", seeker_trait="quick",
                guardian="badger", guardian_type="badger", guardian_trait="wise",
                want="borrow_light", object="lantern", response="gentle_no"),
    StoryParams(setting="brook", seeker="fox", seeker_type="fox", seeker_trait="bright",
                guardian="badger", guardian_type="badger", guardian_trait="patient",
                want="cross_water", object="blanket", response="wait"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.seeker not in CREATURES or params.want not in WANTS or params.object not in OBJECTS:
        raise StoryError("Invalid story parameters.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if RESPONSES[params.response]["sense"] < 2:
        raise StoryError("Response is too rash.")
    if not seek_reasonable(params.seeker, params.want, params.object):
        raise StoryError("That combination does not make a reasonable fable.")
    world = tell(World(), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/3.\n#show safe_response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable/3.\n#show safe_response/1."))
        print("reasonable:", sorted(asp.atoms(model, "reasonable")))
        print("safe responses:", sorted(asp.atoms(model, "safe_response")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
