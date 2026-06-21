#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/abdc_taco_pile_sound_effects_curiosity_foreshadowing.py
========================================================================================

A small standalone storyworld built from the seed words ``abdc``, ``taco``, and
``pile`` with sound effects, curiosity, and foreshadowing. The world is a
child-facing rhyming story about a mysterious little pile, a clue that hints at
what comes next, and a gentle reveal that turns curiosity into understanding.

The world model is intentionally simple but state-driven:
- a child hears sound effects from a taco pile,
- a foreshadowing clue appears before the reveal,
- curiosity pushes the child to investigate,
- a small tumble or tidy discovery changes the ending image.

The script supports the shared Storyweavers CLI contract:
default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
and --show-asp.
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
CURIOUS_MIN = 1.0
RUMBLE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    sound_words: list[str]
    scent: str
    vibe: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    sound: str
    foreshadow: str
    reveal: str
    messy: bool = False
    delicious: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str
    object_id: str
    child: str
    child_gender: str
    parent: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def rhyme_line(*parts: str) -> str:
    return " ".join(p.strip() for p in parts if p.strip())


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    obj = world.get("object")
    if child.memes["curiosity"] < CURIOUS_MIN:
        return out
    sig = ("clue", obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["curiosity"] += 0.5
    obj.meters["attention"] += 1
    out.append(obj.attrs["foreshadow"])
    return out


def _r_rumble(world: World) -> list[str]:
    out: list[str] = []
    obj = world.get("object")
    if obj.meters["tumble"] < THRESHOLD:
        return out
    sig = ("rumble", obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["curiosity"] += 0.5
    world.get("room").meters["mess"] += 1
    out.append(obj.attrs["sound"])
    return out


CAUSAL_RULES = [Rule("clue", _r_clue), Rule("rumble", _r_rumble)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for oid, obj in OBJECTS.items():
            if sid in {"kitchen", "yard"} and oid in {"taco", "abdc"}:
                combos.append((sid, oid))
    return combos


def reason_ok(setting: Setting, obj: ObjectCfg) -> bool:
    return setting.id in {"kitchen", "yard"} and obj.id in {"taco", "abdc"}


def _do_investigate(world: World, child: Entity, obj: Entity, narrate: bool = True) -> None:
    child.memes["curiosity"] += 1
    obj.meters["tumble"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, obj_cfg: ObjectCfg, child_name: str = "Mia", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    room = world.add(Entity(id="room", kind="room", type="room", label=setting.place))
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="curious"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="helper"))
    obj = world.add(Entity(id="object", kind="thing", type="thing", label=obj_cfg.label, role="mystery",
                           attrs={"sound": obj_cfg.sound, "foreshadow": obj_cfg.foreshadow, "reveal": obj_cfg.reveal},
                           tags=set(obj_cfg.tags)))
    child.memes["curiosity"] = 1.5
    world.facts["setting"] = setting
    world.facts["object_cfg"] = obj_cfg
    world.facts["room"] = room
    world.say(rhyme_line(
        f"In {setting.place}, where the warm light played,",
        f"{child_name} saw a little pile and paused in the shade."
    ))
    world.say(rhyme_line(
        f"'{obj_cfg.phrase},' went the clue, soft and small,",
        f"and {setting.sound_words[0]} made the room hear it all."
    ))
    world.para()
    world.say(rhyme_line(
        f"{child_name} leaned in close, with a curious grin,",
        f"to see what the pile was hiding within."
    ))
    _do_investigate(world, child, obj, narrate=True)
    world.para()
    if obj_cfg.messy:
        world.say(rhyme_line(
            f"With a {obj_cfg.sound}, the pile gave way,",
            f"and taco bits tumbled in a bright little sway."
        ))
        world.say(rhyme_line(
            f"The parent came smiling, not cross, not mean,",
            f"and helped scoop the bits till the table shone clean."
        ))
        child.memes["joy"] += 1
        parent.memes["care"] += 1
        world.say(rhyme_line(
            f"Then {child_name} laughed, 'Oh wow!' as the last crumbs fell,",
            f"for curiosity can lead to a story as well."
        ))
    else:
        world.say(rhyme_line(
            f"Under the pile was a note with a cheer,",
            f"and the letters abdc winked like a mirror."
        ))
        world.say(rhyme_line(
            f"It was a taco-game sign, a joke by design,",
            f"with a lunch-time surprise that turned out just fine."
        ))
        child.memes["joy"] += 1
        parent.memes["joy"] += 1
        world.say(rhyme_line(
            f"{child_name} smiled at the clue, then skipped away light,",
            f"with the taco-pile mystery solved just right."
        ))
    world.facts.update(child=child, parent=parent, object=obj, outcome="messy" if obj_cfg.messy else "clean")
    return world


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the kitchen", sound_words=["clink-clack", "tip-tap"], scent="taco spice", vibe="warm"),
    "yard": Setting(id="yard", place="the yard", sound_words=["rustle-rum", "thump-thrum"], scent="sun and dust", vibe="bright"),
}

OBJECTS = {
    "taco": ObjectCfg(
        id="taco",
        label="taco pile",
        phrase="taco pile",
        sound="shuffle-shoo",
        foreshadow="Something golden and crunchy hid in the pile, like a lunch-time drum.",
        reveal="A taco pile can wobble when one shell leans the wrong way.",
        messy=True,
        delicious=True,
        tags={"taco", "pile", "sound", "curiosity", "foreshadowing", "abdc"},
    ),
    "abdc": ObjectCfg(
        id="abdc",
        label="abdc card",
        phrase="abdc",
        sound="flip-flap",
        foreshadow="A tiny card with abdc on it peeked from below the plate.",
        reveal="abdc was only a clue, a tidy sign for the game.",
        messy=False,
        delicious=False,
        tags={"abdc", "sound", "curiosity", "foreshadowing"},
    ),
}

GIRL_NAMES = ["Mia", "Lila", "Nina", "Zoe", "Ava", "Eve"]
BOY_NAMES = ["Finn", "Theo", "Leo", "Max", "Ben", "Owen"]
TRAITS = ["curious", "bright", "gentle", "cheery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s, o = f["setting"], f["object_cfg"]
    return [
        f'Write a rhyming story for a child where "{o.label}" appears with a '
        f'gentle sound effect and a curious clue.',
        f"Tell a small rhyming tale set in {s.place} that uses the words abdc, "
        f"taco, and pile, and lets curiosity lead to a reveal.",
        f"Write a foreshadowing story with sound words where a child notices a "
        f"taco pile, wonders what it means, and gets a sweet surprise.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, obj, setting = f["child"], f["parent"], f["object"], f["setting"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.label} and {child.pronoun('possessive')} {parent.label_word}. "
         f"They share a little scene in {setting.place}."),
        ("What did the child notice?",
         f"{child.label} noticed a {obj.label} and listened for the sound around it. "
         f"That made the child curious about what was hiding there."),
        ("What clue foreshadowed the ending?",
         f"The clue was {obj.attrs['foreshadow']} It hinted that the pile was not just sitting still."),
    ]
    if f["outcome"] == "messy":
        qa.append((
            "What happened when the child investigated?",
            f"The {obj.label} wobbled, made a little sound, and spilled taco bits. "
            f"Curiosity led to a mess, but the parent helped make it tidy again."
        ))
    else:
        qa.append((
            "What happened when the child investigated?",
            f"The child found a tidy abdc card under the pile. The clue turned into a game, "
            f"and the ending stayed neat and bright."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with {child.label} smiling after the reveal. The pile was no longer a mystery, "
        f"and the room felt calm and cheerful."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["object_cfg"].tags)
    out = []
    if "taco" in tags:
        out.append(("What is a taco?", "A taco is a folded food with tasty filling inside a shell or tortilla."))
    if "pile" in tags:
        out.append(("What is a pile?", "A pile is a bunch of things stacked or gathered together."))
    if "sound" in tags:
        out.append(("What is a sound effect?", "A sound effect is a noise that helps tell a story or show what is happening."))
    if "curiosity" in tags:
        out.append(("What is curiosity?", "Curiosity is the wish to learn what something is or why it is there."))
    if "foreshadowing" in tags:
        out.append(("What is foreshadowing?", "Foreshadowing is a clue that hints at what may happen later."))
    if "abdc" in tags:
        out.append(("What is abdc in this story?", "abdc is a little clue card in the story, not a scary secret."))
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", object_id="taco", child="Mia", child_gender="girl", parent="mother"),
    StoryParams(setting="yard", object_id="abdc", child="Finn", child_gender="boy", parent="father"),
]


def explain_rejection(setting: Setting, obj: ObjectCfg) -> str:
    return f"(No story: {obj.label} does not fit this little setting and its clue path.)"


def valid_story(setting: Setting, obj: ObjectCfg) -> bool:
    return reason_ok(setting, obj)


ASP_RULES = r"""
setting_ok(kitchen).
setting_ok(yard).
object_ok(taco).
object_ok(abdc).
valid(S,O) :- setting_ok(S), object_ok(O).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_ok", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object_ok", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False)
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    if rc == 0:
        print("OK: ASP parity and story-generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: abdc, taco, pile, sound, curiosity, foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    object_id = args.object_id or rng.choice(list(OBJECTS))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    if not valid_story(SETTINGS[setting], OBJECTS[object_id]):
        raise StoryError(explain_rejection(SETTINGS[setting], OBJECTS[object_id]))
    return StoryParams(setting=setting, object_id=object_id, child=name, child_gender=child_gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.object_id not in OBJECTS:
        raise StoryError("invalid story parameters")
    world = tell(SETTINGS[params.setting], OBJECTS[params.object_id], params.child, params.child_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/object combos:")
        for s, o in combos:
            print(f"  {s:8} {o}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
