#!/usr/bin/env python3
"""
storyworlds/worlds/whats_moral_value_myth.py
============================================

A small mythic storyworld about a child asking, "what's moral value?" and
discovering it through a concrete trial.

The world is built from a tiny myth-like premise:
- a young seeker asks about moral value
- an elder or spirit answers with a task
- a tempting selfish choice creates tension
- the seeker chooses a value in action
- the ending image shows the value made real

The simulation tracks physical state in meters and social/emotional state in
memes, so the prose is driven by changes rather than a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "sister", "queen", "priestess"}
        masculine = {"boy", "man", "father", "brother", "king", "priest"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    sky: str
    sacred: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Value:
    key: str
    label: str
    virtue: str
    opposite: str
    action: str
    gift: str
    risk: str
    symbol: str


@dataclass
class Artifact:
    key: str
    label: str
    phrase: str
    kind: str
    vulnerable_to: str
    worn_on: str
    value_key: str


@dataclass
class Challenge:
    key: str
    title: str
    temptation: str
    fix: str
    required_value: str
    mess: str
    zone: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.zone = set(self.zone)
        w.facts = dict(self.facts)
        return w


def _m(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _v(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _add_meter(entity: Entity, key: str, amount: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def _add_meme(entity: Entity, key: str, amount: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def setup_world(setting: Setting, value: Value, challenge: Challenge, artifact: Artifact,
                hero_name: str, hero_type: str, elder_type: str) -> World:
    w = World(setting)
    seeker = w.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    elder = w.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder"))
    spirit = w.add(Entity(id="Spirit", kind="character", type="thing", label="the spirit"))
    relic = w.add(Entity(
        id="Relic",
        kind="thing",
        type=artifact.kind,
        label=artifact.label,
        phrase=artifact.phrase,
        owner=seeker.id,
        caretaker=elder.id,
        worn_by=seeker.id,
    ))
    w.facts.update(
        seeker=seeker,
        elder=elder,
        spirit=spirit,
        relic=relic,
        value=value,
        challenge=challenge,
        setting=setting,
    )
    return w


def _predict_loss(world: World, challenge: Challenge, artifact: Artifact) -> bool:
    sim = world.copy()
    seeker = sim.facts["seeker"]
    if challenge.mess == artifact.vulnerable_to:
        _add_meter(seeker, challenge.mess, 1.0)
    return True


def introduce(world: World, seeker: Entity, value: Value) -> None:
    world.say(
        f"{seeker.id} was a small seeker who walked beneath old stars and asked "
        f'whats moral value, as if the night itself might answer.'
    )
    _add_meme(seeker, "wonder", 1.0)
    _add_meme(seeker, "question", 1.0)
    world.say(
        f"The answer came as a name the old people knew: {value.label}. "
        f"It meant {value.virtue} instead of {value.opposite}."
    )


def arrival(world: World, seeker: Entity) -> None:
    world.say(
        f"At {world.setting.place}, the {world.setting.sky} hovered above the "
        f"{world.setting.sacred}, and even the wind seemed to listen."
    )


def desire(world: World, seeker: Entity, challenge: Challenge, value: Value, artifact: Artifact) -> None:
    _add_meme(seeker, "desire", 1.0)
    world.say(
        f"{seeker.id} wanted to {challenge.fix}, but the {challenge.title} was near "
        f"the {artifact.label}, and the {challenge.temptation} was sweet."
    )


def warn(world: World, elder: Entity, seeker: Entity, challenge: Challenge, artifact: Artifact) -> None:
    _add_meme(seeker, "fear", 1.0)
    world.say(
        f'"If you choose the easy path, your {artifact.label} will be {challenge.mess}," '
        f"{elder.label} said. \"A true answer must protect what is good.\""
    )


def test(world: World, seeker: Entity, challenge: Challenge) -> None:
    _add_meter(seeker, challenge.mess, 1.0)
    _add_meme(seeker, "tempted", 1.0)
    world.zone = {challenge.zone}
    world.say(
        f"{seeker.id} reached toward the shining thing, but the thought of keeping it "
        f"for {seeker.pronoun('object')} alone tugged hard."
    )


def resolve(world: World, seeker: Entity, elder: Entity, spirit: Entity, value: Value,
            challenge: Challenge, artifact: Artifact) -> None:
    _add_meme(seeker, value.key, 1.0)
    _add_meme(seeker, "courage", 1.0)
    _add_meme(seeker, "joy", 1.0)
    seeker.memes["tempted"] = 0.0
    world.say(
        f"Then {seeker.id} gave the prize back and chose to {value.action}. "
        f"That choice made the air feel clean."
    )
    world.say(
        f"The {spirit.label} brightened, and the {artifact.label} stayed {artifact.phrase}."
    )
    world.say(
        f"{elder.label} smiled, for moral value was no longer only a question. "
        f"It had become a deed."
    )


def tell(setting: Setting, value: Value, challenge: Challenge, artifact: Artifact,
         hero_name: str = "Nia", hero_type: str = "girl", elder_type: str = "elder") -> World:
    world = setup_world(setting, value, challenge, artifact, hero_name, hero_type, elder_type)
    seeker = world.facts["seeker"]
    elder = world.facts["elder"]
    spirit = world.facts["spirit"]
    relic = world.facts["relic"]

    introduce(world, seeker, value)
    world.para()
    arrival(world, seeker)
    desire(world, seeker, challenge, value, artifact)
    warn(world, elder, seeker, challenge, artifact)
    test(world, seeker, challenge)
    world.para()
    resolve(world, seeker, elder, spirit, value, challenge, artifact)

    world.facts.update(
        seeker=seeker,
        elder=elder,
        spirit=spirit,
        relic=relic,
        value=value,
        challenge=challenge,
        artifact=artifact,
        resolved=True,
    )
    return world


SETTINGS = {
    "temple_hill": Setting(place="the temple hill", sky="golden sky", sacred="stone steps", affords={"return"}),
    "river_shrine": Setting(place="the river shrine", sky="silver mist", sacred="shallow pool", affords={"share"}),
    "oak_grove": Setting(place="the oak grove", sky="green dusk", sacred="old roots", affords={"give"}),
    "market_ruins": Setting(place="the market ruins", sky="red dawn", sacred="broken arch", affords={"speak"}),
}

VALUES = {
    "kindness": Value(
        key="kindness",
        label="Kindness",
        virtue="sharing what you have so another heart can rest",
        opposite="taking and keeping",
        action="share the water with the thirsty child",
        gift="a warm blessing",
        risk="hardening the heart",
        symbol="a bowl of clear water",
    ),
    "truth": Value(
        key="truth",
        label="Truth",
        virtue="saying what is real even when silence would be safer",
        opposite="hiding and twisting",
        action="speak the true name of the relic",
        gift="a clear path",
        risk="living inside a lie",
        symbol="a bright reed",
    ),
    "courage": Value(
        key="courage",
        label="Courage",
        virtue="standing steady while fear is close",
        opposite="running away",
        action="carry the lantern through the dark place",
        gift="the road home",
        risk="letting fear rule",
        symbol="a small bronze lamp",
    ),
    "mercy": Value(
        key="mercy",
        label="Mercy",
        virtue="forgiving when anger asks for a harder answer",
        opposite="vengeance",
        action="free the prisoner instead of boasting",
        gift="peace in the chest",
        risk="turning justice into cruelty",
        symbol="a white ribbon",
    ),
}

CHALLENGES = {
    "sharing": Challenge(
        key="sharing",
        title="the thirsty child",
        temptation="keep the water jar for yourself",
        fix="share the jar",
        required_value="kindness",
        mess="dusty",
        zone="hands",
    ),
    "truth_test": Challenge(
        key="truth_test",
        title="the hidden name",
        temptation="keep the secret and look wise",
        fix="speak the true name",
        required_value="truth",
        mess="clouded",
        zone="mouth",
    ),
    "dark_road": Challenge(
        key="dark_road",
        title="the dark road",
        temptation="turn back and let the others go first",
        fix="walk on with the lantern",
        required_value="courage",
        mess="shaken",
        zone="feet",
    ),
    "prison_gate": Challenge(
        key="prison_gate",
        title="the prisoner at the gate",
        temptation="boast and demand a reward",
        fix="open the gate gently",
        required_value="mercy",
        mess="stained",
        zone="hands",
    ),
}

ARTIFACTS = {
    "jar": Artifact(
        key="jar",
        label="water jar",
        phrase="still clear",
        kind="jar",
        vulnerable_to="dusty",
        worn_on="hands",
        value_key="kindness",
    ),
    "name_stone": Artifact(
        key="name_stone",
        label="name-stone",
        phrase="bright with honest light",
        kind="stone",
        vulnerable_to="clouded",
        worn_on="mouth",
        value_key="truth",
    ),
    "lantern": Artifact(
        key="lantern",
        label="lantern",
        phrase="bright and unbroken",
        kind="lantern",
        vulnerable_to="shaken",
        worn_on="feet",
        value_key="courage",
    ),
    "key": Artifact(
        key="key",
        label="bronze key",
        phrase="safe in the hand",
        kind="key",
        vulnerable_to="stained",
        worn_on="hands",
        value_key="mercy",
    ),
}

GIRL_NAMES = ["Nia", "Ari", "Lina", "Mira", "Sana", "Tia"]
BOY_NAMES = ["Ari", "Doran", "Levi", "Mako", "Taro", "Soren"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, s in SETTINGS.items():
        for c_id, c in CHALLENGES.items():
            for a_id, a in ARTIFACTS.items():
                if c.required_value == a.value_key:
                    combos.append((s_id, c_id, a_id))
    return combos


@dataclass
class StoryParams:
    place: str
    challenge: str
    artifact: str
    value: str
    name: str
    gender: str
    elder: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic moral-value storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["elder", "priest", "queen", "king"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.value and args.artifact and VALUES[args.value].key != ARTIFACTS[args.artifact].value_key:
        raise StoryError("Chosen artifact does not fit the chosen moral value.")
    filtered = [c for c in combos
                if (args.place is None or c[0] == args.place)
                and (args.challenge is None or c[1] == args.challenge)
                and (args.artifact is None or c[2] == args.artifact)]
    if not filtered:
        raise StoryError("No valid mythic combination matches those options.")
    place, challenge, artifact = rng.choice(sorted(filtered))
    value = args.value or ARTIFACTS[artifact].value_key
    if args.gender:
        gender = args.gender
    else:
        gender = rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["elder", "priest", "queen", "king"])
    return StoryParams(place=place, challenge=challenge, artifact=artifact, value=value,
                       name=name, gender=gender, elder=elder)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth for a child that asks "whats moral value?" and answers through the value of {f["value"].label}.',
        f"Tell a short mythic tale where {f['seeker'].id} learns {f['value'].label} at {world.setting.place}.",
        f"Create a gentle legend about choosing {f['value'].virtue} instead of {f['value'].opposite}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker, elder, value, challenge, artifact = f["seeker"], f["elder"], f["value"], f["challenge"], f["artifact"]
    return [
        QAItem(
            question=f"What did {seeker.id} ask about at the start?",
            answer=f"{seeker.id} asked whats moral value, and the story answered with {value.label}.",
        ),
        QAItem(
            question=f"Why did {elder.label} warn {seeker.id}?",
            answer=f"{elder.label} warned {seeker.id} because the easy choice would have left the {artifact.label} {challenge.mess}.",
        ),
        QAItem(
            question=f"What did {seeker.id} choose instead of the temptation?",
            answer=f"{seeker.id} chose to {value.action}. That was the moral value made into action.",
        ),
        QAItem(
            question=f"What stayed safe by the end?",
            answer=f"The {artifact.label} stayed {artifact.phrase}, because {seeker.id} chose {value.label} instead of {value.opposite}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    v = world.facts["value"]
    return [
        QAItem(
            question=f"What is {v.label}?",
            answer=f"{v.label} is the virtue of {v.virtue}.",
        ),
        QAItem(
            question=f"Why do myths often use signs and tests?",
            answer="Myths use signs and tests to show a big idea as something a person can do, see, and remember.",
        ),
        QAItem(
            question=f"What is a moral value?",
            answer="A moral value is a good rule for how to live and treat others, like kindness, truth, courage, or mercy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], VALUES[params.value], CHALLENGES[params.challenge],
                 ARTIFACTS[params.artifact], params.name, params.gender, params.elder)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
value_ok(P, V) :- artifact(P), value(V), value_key(P, V).
valid(Place, Challenge, Artifact) :- setting(Place), challenge(Challenge), artifact(Artifact),
                                     challenge_value(Challenge, V), value_key(Artifact, V),
                                     affords(Place, Challenge).
#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("challenge_value", cid, c.required_value))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("value_key", aid, a.value_key))
    for vid, v in VALUES.items():
        lines.append(asp.fact("value", vid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="temple_hill", challenge="sharing", artifact="jar", value="kindness",
                name="Nia", gender="girl", elder="elder"),
    StoryParams(place="river_shrine", challenge="truth_test", artifact="name_stone", value="truth",
                name="Ari", gender="boy", elder="priest"),
    StoryParams(place="oak_grove", challenge="dark_road", artifact="lantern", value="courage",
                name="Lina", gender="girl", elder="queen"),
    StoryParams(place="market_ruins", challenge="prison_gate", artifact="key", value="mercy",
                name="Soren", gender="boy", elder="king"),
]


def explain_rejection(challenge: Challenge, artifact: Artifact) -> str:
    return (
        f"(No story: the {challenge.title} does not test {artifact.label} for the "
        f"right value. In this world, the chosen artifact must match the moral value "
        f"hidden in the challenge.)"
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.value} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
