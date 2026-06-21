#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/molt_uranium_tortilla_magic_sound_effects_repetition.py
======================================================================================

A small ghost-story world for the seed words **molt**, **uranium**, and
**tortilla**, with magic, sound effects, and repetition.

Premise:
A child hears strange sounds in a haunted kitchen, discovers that a magic trick
made a glowing tortilla "molt" its soot-like skin, and learns the eerie thing is
just a safe, silly illusion around a shiny uranium pebble kept inside a sealed
lantern.

The world simulates a tiny sequence:
premise -> unease -> magical repeat-pattern -> reveal -> calmer ending.

It is written as a standalone Storyweavers world script and supports the shared
CLI contract: default generation, -n, --all, --seed, --trace, --qa, --json,
--asp, --verify, and --show-asp.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    dark: str
    echoes: str
    moonlight: str
    atmosphere: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    glow: str
    safe: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicCfg:
    id: str
    label: str
    effect: str
    repeat: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundCfg:
    id: str
    label: str
    onomatopoeia: str
    feel: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_unease(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["fear"] < THRESHOLD:
        return out
    if ("unease",) in world.fired:
        return out
    world.fired.add(("unease",))
    world.get("room").meters["cold"] += 1
    world.get("room").memes["unease"] += 1
    out.append("__unease__")
    return out


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    if world.get("tortilla").meters["magic"] < THRESHOLD:
        return out
    if ("repeat",) in world.fired:
        return out
    world.fired.add(("repeat",))
    world.get("tortilla").meters["shine"] += 1
    world.get("child").memes["wonder"] += 1
    out.append("__repeat__")
    return out


CAUSAL_RULES = [
    Rule("unease", "mood", _r_unease),
    Rule("repeat", "magic", _r_repeat),
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


def story_open(world: World, child: Entity, room: Setting) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a moon-white night, {child.id} crept into {room.place}. "
        f"{room.atmosphere} {room.echoes}"
    )
    world.say(
        f'The air felt wrong, as if it were listening back. "Tap-tap," went the floor.'
    )


def find_glow(world: World, child: Entity, object_cfg: ObjectCfg) -> None:
    child.memes["fear"] += 1
    world.say(
        f'On the counter sat {object_cfg.phrase}. It gave off a thin {object_cfg.glow}, '
        f"quiet and strange."
    )
    world.say(
        f'"What is that?" {child.id} whispered. "What is that? What is that?"'
    )


def magic_whisper(world: World, child: Entity, magic: MagicCfg, sound: SoundCfg) -> None:
    world.get("tortilla").meters["magic"] += 1
    world.say(
        f"{magic.label.capitalize()} answered with a soft {sound.onomatopoeia}. "
        f"{magic.effect} {magic.repeat}"
    )


def reveal(world: World, child: Entity, object_cfg: ObjectCfg, magic: MagicCfg) -> None:
    world.get("child").memes["fear"] = max(0.0, world.get("child").memes["fear"] - 1)
    world.say(
        f"Then the {magic.label} did something silly and bright: it made the "
        f"{object_cfg.label} molted with a papery little curl, and underneath was "
        f"nothing scary at all."
    )
    world.say(
        f"It was just a glowing trick, hiding a tiny sealed lantern with a shiny "
        f"uranium pebble inside."
    )


def calm_end(world: World, child: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    world.say(
        f'{child.id} let out one long breath. "Ha-ha, ha-ha, ha-ha," {child.id} said, '
        f"and the room sounded friendly again."
    )
    world.say(
        "The floor stopped creaking. The moon kept shining. The little glow sat still, "
        "and nothing reached out from the dark."
    )


def tell(setting: Setting, object_cfg: ObjectCfg, magic: MagicCfg, sound: SoundCfg,
         response: Response, child_name: str = "Mina", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    toy = world.add(Entity(id="tortilla", type="object", label=object_cfg.label))
    world.add(Entity(id="uranium", type="mineral", label="uranium pebble"))
    world.facts.update(setting=setting, object_cfg=object_cfg, magic=magic, sound=sound, response=response)

    story_open(world, child, setting)
    find_glow(world, child, object_cfg)
    world.para()
    magic_whisper(world, child, magic, sound)
    child.memes["fear"] += 1
    propagate(world, narrate=False)
    world.say(f'"{sound.onomatopoeia}" echoed again. {magic.repeat}')
    world.para()
    if response.power >= 1:
        reveal(world, child, object_cfg, magic)
        calm_end(world, child)
        outcome = "reveal"
    else:
        world.say(
            f"The glow only got stranger. {response.fail} The little room stayed full "
            f"of shadows."
        )
        outcome = "unclear"
    world.facts["outcome"] = outcome
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["room"] = room
    world.facts["tortilla"] = toy
    return world


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the old kitchen",
        dark="the pantry corner",
        echoes="Somewhere, a spoon chimed: ting... ting... ting.",
        moonlight="moonlight",
        atmosphere="The cabinets were shut tight, and the refrigerator hummed.",
        tags={"ghost", "kitchen"},
    ),
    "cellar": Setting(
        id="cellar",
        place="the cellar stairs",
        dark="the bottom step",
        echoes="From below came a soft clonk, clonk, clonk.",
        moonlight="moonlight",
        atmosphere="The stone felt cool and the shadows leaned long.",
        tags={"ghost", "cellar"},
    ),
}

OBJECTS = {
    "tortilla": ObjectCfg(
        id="tortilla",
        label="tortilla",
        phrase="a tortilla on a blue plate",
        glow="greenish shimmer",
        safe=True,
        tags={"tortilla"},
    ),
    "blanket": ObjectCfg(
        id="blanket",
        label="tortilla blanket",
        phrase="a tortilla-shaped cloth bundle",
        glow="moon-pale shimmer",
        safe=True,
        tags={"tortilla"},
    ),
}

MAGICS = {
    "molt": MagicCfg(
        id="molt",
        label="the molt spell",
        effect="The tortilla shed its dark skin like a sleepy ghost shedding a cloak.",
        repeat="Again and again, the trick went molt, molt, molt.",
        reveal="It was only a reveal spell.",
        tags={"molt", "magic"},
    ),
    "rebound": MagicCfg(
        id="rebound",
        label="the repeat spell",
        effect="Every whisper came back twice, then three times, as if the room loved to echo.",
        repeat="Repeat, repeat, repeat.",
        reveal="It was only a looping charm.",
        tags={"repetition", "magic"},
    ),
}

SOUNDS = {
    "boo": SoundCfg(
        id="boo",
        label="a boo sound",
        onomatopoeia="Boo... boo... boo...",
        feel="spooky",
        tags={"sound"},
    ),
    "clink": SoundCfg(
        id="clink",
        label="a clinking sound",
        onomatopoeia="Clink-clink!",
        feel="tinny",
        tags={"sound"},
    ),
}

RESPONSES = {
    "reveal": Response(
        id="reveal",
        sense=3,
        power=3,
        text="looked closer and saw the trick for what it was",
        fail="tried to explain it, but the mystery stayed tangled",
        qa_text="looked closer and saw that the trick was only a harmless glow",
        tags={"magic"},
    ),
    "wait": Response(
        id="wait",
        sense=2,
        power=2,
        text="waited for the sound to repeat one more time, then smiled",
        fail="waited, but the room only grew quieter and more eerie",
        qa_text="waited and listened until the repetition gave the trick away",
        tags={"sound"},
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Iris", "Nora", "June"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Finn", "Theo"]
TRAITS = ["curious", "careful", "brave", "quiet"]


@dataclass
class StoryParams:
    setting: str
    object_cfg: str
    magic: str
    sound: str
    response: str
    child_name: str
    child_gender: str
    parent_type: str
    trait: str = "curious"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for oid in OBJECTS:
            for mid in MAGICS:
                for snd in SOUNDS:
                    for rid in RESPONSES:
                        combos.append((sid, oid, mid, snd, rid))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.object_cfg not in OBJECTS:
        raise StoryError("Unknown object.")
    if params.magic not in MAGICS:
        raise StoryError("Unknown magic.")
    if params.sound not in SOUNDS:
        raise StoryError("Unknown sound.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with magic, sound effects, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_cfg", choices=OBJECTS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    object_cfg = args.object_cfg or rng.choice(list(OBJECTS))
    magic = args.magic or rng.choice(list(MAGICS))
    sound = args.sound or rng.choice(list(SOUNDS))
    response = args.response or rng.choice(list(RESPONSES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(setting=setting, object_cfg=object_cfg, magic=magic, sound=sound, response=response,
                         child_name=name, child_gender=gender, parent_type=parent, trait=trait)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    if params.object_cfg not in OBJECTS:
        raise StoryError("Invalid object.")
    if params.magic not in MAGICS:
        raise StoryError("Invalid magic.")
    if params.sound not in SOUNDS:
        raise StoryError("Invalid sound.")
    if params.response not in RESPONSES:
        raise StoryError("Invalid response.")
    world = tell(
        SETTINGS[params.setting],
        OBJECTS[params.object_cfg],
        MAGICS[params.magic],
        SOUNDS[params.sound],
        RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a 3-to-5-year-old that includes the words "molt", "uranium", and "tortilla".',
        f"Tell a spooky-but-safe story where {f['child'].id} hears echoing sounds in {f['setting'].place} and discovers a magic tortilla trick.",
        f"Write a repetition-heavy haunted-kitchen story with a harmless reveal and one glowing tortilla.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    obj = f["object_cfg"]
    magic = f["magic"]
    snd = f["sound"]
    qas = [
        ("Where did the story happen?",
         f"It happened in {setting.place}. The place felt spooky because it was quiet, dim, and full of echoing little noises."),
        ("What strange thing did the child see?",
         f"{child.id} saw {obj.phrase}, and it gave off a greenish shimmer. That glow made the room feel ghostly at first."),
        ("What repeated sound did the child hear?",
         f"{snd.onomatopoeia} kept coming back. The repetition made the child think something mysterious was nearby."),
        ("What was the magical trick?",
         f"It was {magic.label}. The spell made the tortilla seem to molt and change, which looked eerie before the trick was explained."),
    ]
    if f.get("outcome") == "reveal":
        qas.append((
            "How did the story end?",
            "The child looked closer and found that the scary-looking thing was only a harmless trick. The glowing uranium pebble stayed sealed away, and the room felt friendly again."
        ))
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set()
    tags |= set(f["object_cfg"].tags)
    tags |= set(f["magic"].tags)
    tags |= set(f["sound"].tags)
    out = []
    if "tortilla" in tags:
        out.append(("What is a tortilla?",
                    "A tortilla is a flat soft bread, often made from corn or flour. People use it for wraps or to eat with food."))
    if "molt" in tags:
        out.append(("What does molt mean?",
                    "To molt means to shed an old outer layer. Some animals molt feathers or skin, and a magic story can borrow that word for a spooky change."))
    if "sound" in tags:
        out.append(("What are sound effects?",
                    "Sound effects are made-up or recorded noises used to make a story feel real, spooky, or fun. In a tale they can repeat, echo, or surprise you."))
    if "magic" in tags:
        out.append(("Why do magic tricks feel mysterious?",
                    "Magic tricks hide the answer for a moment and then show a reveal. That surprise is what makes them feel mysterious."))
    out.append(("Is uranium a toy?",
                "No. Uranium is not a toy, and children should never play with unknown glowing materials. In this story it stays sealed away like a tiny prop in a safe lantern."))
    return out


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", object_cfg="tortilla", magic="molt", sound="boo",
                response="reveal", child_name="Mina", child_gender="girl", parent_type="mother",
                trait="curious"),
    StoryParams(setting="cellar", object_cfg="tortilla", magic="rebound", sound="clink",
                response="wait", child_name="Owen", child_gender="boy", parent_type="father",
                trait="careful"),
]


def explain_rejection() -> str:
    return "(No story: the seed words are all available, but the requested combination was invalid.)"


ASP_RULES = r"""
tension :- fear(child).
echoing :- sound_effect(S), repeated(S).
revealed :- magic_spell(M), repeat_pattern(M).
outcome(reveal) :- tension, echoing, revealed.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for mid in MAGICS:
        lines.append(asp.fact("magic_spell", mid))
    for sid in SOUNDS:
        lines.append(asp.fact("sound_effect", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    program = asp_program("#show outcome/1.")
    model = asp.one_model(program)
    _ = asp.atoms(model, "outcome")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        return 1
    print("OK: ASP loaded and story generation smoke test passed.")
    return 0


def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program("#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP twin is minimal for this world.")
        print(asp_program("#show outcome/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
                params = build_story_params_from_args(args, random.Random(seed))
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
            header = f"### {p.child_name}: {p.setting} / {p.magic} / {p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
