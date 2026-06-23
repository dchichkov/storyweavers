#!/usr/bin/env python3
"""
storyworlds/worlds/refuge_yoga_transfix_magic_transformation_mystery.py
=======================================================================

A standalone storyworld about a child who finds a quiet refuge, tries yoga to
stay calm, and gets transfix by a mystery that turns out to involve magic and a
transformation.

The domain is small on purpose: a place of refuge, a puzzling magical object,
a calming yoga practice, and a transformation that reveals the answer.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    helper: bool = False
    magical: bool = False
    transformable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    refuge: bool
    calm: bool
    affords: set[str] = field(default_factory=set)
    hides: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    lure: str
    reveal: str
    magic: bool = False
    transform: bool = False
    affects: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Practice:
    id: str
    label: str
    phrase: str
    pose: str
    soothe: str
    aid: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Turn:
    id: str
    label: str
    reveal: str
    ending_image: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.hidden_room: str = ""

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.hidden_room = self.hidden_room
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_magic(world: World) -> list[str]:
    out = []
    clue = world.get("clue")
    if clue.meters["noticed"] < THRESHOLD:
        return out
    sig = ("magic", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["glimmer"] += 1
    world.get("child").memes["wonder"] += 1
    out.append("__magic__")
    return out


def _r_transform(world: World) -> list[str]:
    out = []
    clue = world.get("clue")
    if clue.meters["glimmer"] < THRESHOLD:
        return out
    sig = ("transform", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.transformable = False
    clue.attrs["revealed"] = True
    world.get("room").meters["secret"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule("magic", "mystery", _r_magic),
    Rule("transform", "mystery", _r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def calm_setup(world: World, child: Entity, place: Place, practice: Practice) -> None:
    child.memes["worry"] += 1
    child.memes["calm"] += 1
    world.say(
        f"{child.id} had found a quiet refuge at {place.label}. "
        f"The place felt still, but something odd kept pulling at {child.pronoun('possessive')} eyes."
    )
    world.say(
        f"To stay brave, {child.id} tried {practice.phrase}; {practice.soothe}."
    )


def notice_clue(world: World, child: Entity, clue: Mystery) -> None:
    child.meters["seen"] += 1
    child.meters["noticed"] += 1
    clue.meters["noticed"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"Then {child.id} spotted {clue.phrase}. {clue.lure}."
    )


def transfix(world: World, child: Entity, clue: Mystery) -> None:
    child.memes["transfix"] += 1
    world.say(
        f"{child.id} stood very still, almost transfix, as the little mystery seemed to glow."
    )


def reveal(world: World, child: Entity, clue: Mystery, turn: Turn) -> None:
    world.say(
        f"When {child.id} looked closer, the secret changed shape. {turn.reveal}"
    )
    world.say(turn.ending_image)
    child.memes["relief"] += 1
    child.memes["joy"] += 1


def tell(place: Place, practice: Practice, mystery: Mystery, turn: Turn,
         child_name: str = "Mina", child_type: str = "girl") -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="observer"))
    helper = world.add(Entity(id="helper", kind="character", type="mother", label="the librarian", helper=True))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="thing",
        label=mystery.label,
        phrase=mystery.phrase,
        magical=mystery.magic,
        transformable=mystery.transform,
    ))
    room = world.add(Entity(id="room", kind="thing", type="room", label=place.label))
    world.hidden_room = "back room"

    calm_setup(world, child, place, practice)
    world.para()
    notice_clue(world, child, mystery)
    transfix(world, child, mystery)
    propagate(world, narrate=False)
    world.para()
    helper.memes["kind"] += 1
    if mystery.transform:
        reveal(world, child, mystery, turn)
    else:
        world.say(f"{helper.label_word.capitalize()} smiled and opened the next door, but the answer stayed hidden.")
    world.facts.update(
        child=child, helper=helper, clue=clue, room=room, place=place,
        practice=practice, mystery=mystery, turn=turn
    )
    return world


@dataclass
class StoryParams:
    place: str = "library"
    practice: str = "breathing"
    mystery: str = "silver_key"
    turn: str = "lantern"
    name: str = "Mina"
    gender: str = "girl"
    seed: Optional[int] = None


PLACES = {
    "library": Place(id="library", label="the old library", refuge=True, calm=True, affords={"yoga", "mystery"}, hides={"secret_room"}),
    "greenhouse": Place(id="greenhouse", label="the quiet greenhouse", refuge=True, calm=True, affords={"yoga", "mystery"}, hides={"hidden_path"}),
    "attic": Place(id="attic", label="the dusty attic", refuge=True, calm=False, affords={"mystery"}, hides={"trapdoor"}),
}


PRACTICES = {
    "breathing": Practice(id="breathing", label="breathing", phrase="slow breathing yoga", pose="easy pose", soothe="the slow breaths made the room feel less scary", aid="a calm mind", tags={"yoga"}),
    "stretching": Practice(id="stretching", label="stretching", phrase="gentle yoga stretches", pose="star pose", soothe="the stretches loosened the worry in her shoulders", aid="steady hands", tags={"yoga"}),
    "balance": Practice(id="balance", label="balance", phrase="careful balance yoga", pose="tree pose", soothe="the balance pose helped her feet feel planted", aid="quiet courage", tags={"yoga"}),
}


MYSTERIES = {
    "silver_key": Mystery(id="silver_key", label="a silver key", phrase="a silver key on the shelf", lure="It looked as if it had been waiting for someone", reveal="The key was not just metal; it was a tiny spell in disguise.", magic=True, transform=True, affects="door", tags={"magic", "transformation"}),
    "paper_bird": Mystery(id="paper_bird", label="a folded paper bird", phrase="a folded paper bird tucked into a book", lure="Its wings seemed to tremble when the light changed", reveal="The paper bird unfolded into a map, as if magic had woken it up.", magic=True, transform=True, affects="map", tags={"magic", "transformation"}),
    "glass_seed": Mystery(id="glass_seed", label="a glass seed", phrase="a glass seed in a bowl of moss", lure="It sparkled like it knew a secret", reveal="The glass seed softened and became a small green sprout.", magic=True, transform=True, affects="sprout", tags={"magic", "transformation"}),
    "music_box": Mystery(id="music_box", label="a tiny music box", phrase="a tiny music box under a cloth", lure="A faint tune leaked out like a whisper", reveal="When it opened, the box transformed into a little mirror that showed the hiding place.", magic=True, transform=True, affects="mirror", tags={"magic", "transformation"}),
}

TURNS = {
    "lantern": Turn(id="lantern", label="lantern", reveal="A hidden lantern clicked on inside the object, and the glow made the trick plain.", ending_image="At the end, a warm little light rested on the table, and the mystery had become something easy to see.", power=3, sense=3, tags={"magic"}),
    "map": Turn(id="map", label="map", reveal="The object shifted and turned into a map, pointing to the hidden room.", ending_image="At the end, the map lay flat and clear, with one dark path marked in gold.", power=2, sense=2, tags={"transformation"}),
    "sprout": Turn(id="sprout", label="sprout", reveal="The object softened into a sprout, and the room smelled fresh as a garden after rain.", ending_image="At the end, a small green sprout sat where the mystery had been, proving it had changed.", power=2, sense=2, tags={"transformation"}),
    "mirror": Turn(id="mirror", label="mirror", reveal="The object became a little mirror, and the reflection showed the missing clue at once.", ending_image="At the end, the mirror caught the light, and the answer shone back from its glass.", power=3, sense=3, tags={"magic"}),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ivy", "Ruby", "Ella", "Zoe", "Maya"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Owen", "Leo", "Finn", "Ben", "Sam"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES:
        for pr in PRACTICES:
            for m in MYSTERIES:
                for t in TURNS:
                    combos.append((p, pr, m, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with refuge, yoga, transfix, magic, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--practice", choices=PRACTICES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--turn", choices=TURNS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.practice is None or c[1] == args.practice)
              and (args.mystery is None or c[2] == args.mystery)
              and (args.turn is None or c[3] == args.turn)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, practice, mystery, turn = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, practice=practice, mystery=mystery, turn=turn, name=name, gender=gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle mystery story that includes the words "refuge", "yoga", and "transfix".',
        f"Tell a child-sized magical mystery set at {f['place'].label} where {f['child'].id} uses {f['practice'].phrase} before the secret changes shape.",
        f"Write a story about a quiet refuge, a yoga practice, and a magical transformation that helps {f['child'].id} solve a mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["child"]
    place = f["place"]
    pr = f["practice"]
    m = f["mystery"]
    t = f["turn"]
    return [
        QAItem(
            question=f"Why did {c.id} use {pr.label} at {place.label}?",
            answer=f"{c.id} used {pr.phrase} because the place felt like a refuge but the mystery made {c.pronoun('possessive')} heart jump. The yoga helped {c.id} stay calm enough to look closely.",
        ),
        QAItem(
            question=f"What made {c.id} almost transfix in the middle of the story?",
            answer=f"{m.phrase} made {c.id} almost transfix because it looked ordinary at first but felt magical. That strange feeling pulled {c.id}'s eyes toward the clue until the secret could be seen.",
        ),
        QAItem(
            question=f"How did the mystery change at the end?",
            answer=f"It changed with magic and transformation: {t.reveal} The ending image proved the clue had become something new and useful.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a refuge?",
            answer="A refuge is a safe place where someone can rest, hide, or feel protected for a while.",
        ),
        QAItem(
            question="What is yoga?",
            answer="Yoga is a way of moving and breathing that can help a person feel calm, steady, and focused.",
        ),
        QAItem(
            question="What does transfix mean?",
            answer="To transfix someone means to hold their attention so strongly that they cannot look away.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a big change, when one thing becomes another thing or looks completely different.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a surprising power that can make ordinary things do impossible or wonderful things.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
noticed_magic(C) :- child(C), clue(X), noticed(X).
transfixed(C) :- noticed_magic(C), child(C).
transformed(X) :- clue(X), glimmer(X), magic(X).
ending(X) :- transformed(X).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.refuge:
            lines.append(asp.fact("refuge", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for prid, pr in PRACTICES.items():
        lines.append(asp.fact("practice", prid))
        for t in sorted(pr.tags):
            lines.append(asp.fact("tag", prid, t))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("clue", mid))
        if m.magic:
            lines.append(asp.fact("magic", mid))
        if m.transform:
            lines.append(asp.fact("transformable", mid))
    lines.append(asp.fact("child", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show transformed/1.\n#show transfixed/1."))
    atoms = set((s.name, tuple(a.name if hasattr(a, "name") else getattr(a, "string", None) for a in s.arguments)) for s in model)
    ok = True
    if not any(name == "transformed" for name, _ in atoms):
        ok = False
    if ok:
        print("OK: ASP program solved.")
    else:
        print("MISMATCH: ASP program failed.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, practice=None, mystery=None, turn=None, name=None, gender=None), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generation smoke test crashed: {exc}")
        return 1
    return 0


def generate(params: StoryParams) -> StorySample:
    place = PLACES.get(params.place)
    practice = PRACTICES.get(params.practice)
    mystery = MYSTERIES.get(params.mystery)
    turn = TURNS.get(params.turn)
    if not place or not practice or not mystery or not turn:
        raise StoryError("Invalid story params.")
    world = tell(place, practice, mystery, turn, params.name, params.gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show transformed/1.\n#show transfixed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} valid combos.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="library", practice="breathing", mystery="silver_key", turn="lantern", name="Mina", gender="girl"),
            StoryParams(place="greenhouse", practice="stretching", mystery="paper_bird", turn="map", name="Owen", gender="boy"),
            StoryParams(place="attic", practice="balance", mystery="glass_seed", turn="sprout", name="Lina", gender="girl"),
            StoryParams(place="library", practice="balance", mystery="music_box", turn="mirror", name="Theo", gender="boy"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
