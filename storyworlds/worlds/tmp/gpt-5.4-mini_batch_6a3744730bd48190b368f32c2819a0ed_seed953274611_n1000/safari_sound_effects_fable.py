#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/safari_sound_effects_fable.py
=============================================================

A small, fable-like safari story world where sound effects matter.

Premise:
A young animal on a safari trail wants to make a loud, playful sound to join
the animals' chorus. A wiser animal warns that the wrong sound can scare a
baby animal or call danger closer. The story turns when the animals choose a
better, rhythmic sound that helps, calms, and brings everyone together.

This script is standalone and uses only the standard library plus the shared
storyworld result containers. It also includes an inline ASP twin for parity
checks and a Python reasonableness gate.
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
SOUND_MIN = 2


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
    can_make_sound: bool = False
    can_soothe: bool = False
    can_warn: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "lioness", "elephant"}
        male = {"boy", "father", "man", "lion", "monkey"}
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
    detail: str
    sounds: list[str] = field(default_factory=list)


@dataclass
class Sound:
    id: str
    label: str
    sound: str
    effect: str
    safe: bool = True
    volume: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Animal:
    id: str
    type: str
    role: str
    label: str
    traits: list[str] = field(default_factory=list)
    age: int = 0
    can_warn: bool = False
    can_lead: bool = False
    can_make_sound: bool = False
    can_soothe: bool = False


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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str = "savanna"
    child: str = "Miri"
    child_type: str = "monkey"
    guide: str = "Asha"
    guide_type: str = "lioness"
    sound: str = "drum"
    response: str = "soft_drum"
    seed: Optional[int] = None


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_attention(world: World) -> list[str]:
    out: list[str] = []
    if world.get("trail").meters["alarm"] >= THRESHOLD and "attention" not in world.fired:
        world.fired.add(("attention",))
        world.get("child").memes["fear"] += 1
        out.append("__attention__")
    return out


def _r_soothe(world: World) -> list[str]:
    out: list[str] = []
    if world.get("baby").memes["startle"] >= THRESHOLD and "soothe" not in world.fired:
        world.fired.add(("soothe",))
        world.get("baby").memes["calm"] += 1
        out.append("__soothe__")
    return out


CAUSAL_RULES = [Rule("attention", _r_attention), Rule("soothe", _r_soothe)]


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


def sound_is_reasonable(sound: Sound, setting: Setting) -> bool:
    return sound.safe and (sound.id in setting.sounds or sound.id == "drum")


def best_response() -> Sound:
    return max(SOUNDS.values(), key=lambda s: s.volume)


def outcome_of(params: StoryParams) -> str:
    if params.sound == "whistle":
        return "warned"
    if params.response == "soft_drum":
        return "guided"
    return "rattled"


def setting_for(key: str) -> Setting:
    try:
        return SETTINGS[key]
    except KeyError as err:
        raise StoryError(f"Unknown setting: {key}") from err


def sound_for(key: str) -> Sound:
    try:
        return SOUNDS[key]
    except KeyError as err:
        raise StoryError(f"Unknown sound: {key}") from err


def _make_story(world: World) -> None:
    child = world.get("child")
    guide = world.get("guide")
    setting = world.get("setting")
    baby = world.get("baby")
    trail = world.get("trail")
    chosen = world.get("sound")
    response = world.get("response")

    child.memes["joy"] += 1
    guide.memes["patience"] += 1

    world.say(
        f"On a bright safari path, {child.id} and {guide.id} walked under the wide sky. "
        f"{setting.label_word.capitalize()} stretched ahead, and the tall grass whispered around them."
    )
    world.say(
        f"{child.id} loved the music of the place. {setting.detail} "
        f'"{chosen.label}!" {child.id} cried. "{chosen.sound}" echoed across the trail.'
    )

    world.para()
    world.say(
        f"But near the path, a little {baby.type} dozed beside its mother. "
        f"The wrong sound could wake it in a fright, and the trail already felt jumpy."
    )

    if chosen.id == "whistle":
        trail.meters["alarm"] += 1
        baby.memes["startle"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{guide.id} lifted a careful hand. "{guide.id}, not that one," {guide.pronoun()} said softly. '
            f'"A whistle is too sharp here. It can scatter the little ones."'
        )
        world.say(
            f"{child.id} lowered the whistle at once and listened."
        )
    else:
        world.say(
            f'{guide.id} smiled and said, "{child.id}, the loudest sound is not always the kindest." '
            f'"Listen for a sound that leads instead of scares."'
        )
        world.say(
            f"{child.id} looked at the drum and nodded."
        )

    world.para()
    if response.id == "soft_drum":
        child.memes["pride"] += 1
        guide.memes["joy"] += 1
        baby.memes["calm"] += 1
        world.say(
            f"Then {child.id} tapped the drum in a gentle beat: {response.sound}. "
            f"The rhythm rolled down the trail like soft footsteps."
        )
        world.say(
            f"The baby lifted its head, blinked once, and settled again. "
            f"{guide.id} joined in, and soon the whole safari path kept time together."
        )
        world.say(
            f"That day {child.id} learned that a wise sound can be strong without being harsh."
        )
    elif response.id == "call_and_wait":
        child.memes["calm"] += 1
        guide.memes["joy"] += 1
        world.say(
            f"Instead of hurrying, {child.id} stood still and made a small waiting sound: {response.sound}. "
            f"It was barely louder than the wind."
        )
        world.say(
            f"The baby stayed asleep, and {guide.id} praised {child.id} for patience. "
            f"On safari, the quietest choice can be the bravest one."
        )
    else:
        world.say(
            f"{child.id} tried another sound, but the trail was still restless. "
            f"Only after {guide.id} showed how to keep the beat did the path grow calm."
        )

    world.say(
        f"In the end, the safari was full of music, but it was music that helped rather than hurt."
    )

    world.facts.update(
        child=child,
        guide=guide,
        setting=setting,
        baby=baby,
        trail=trail,
        sound=chosen,
        response=response,
        outcome=outcome_of(world.facts["params"]),
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = world.add(Entity(id="setting", kind="place", type="place", label=SETTINGS[params.setting].place))
    sound = world.add(Entity(id="sound", kind="thing", type="sound", label=SOUNDS[params.sound].label, can_make_sound=True))
    response = world.add(Entity(id="response", kind="thing", type="response", label=SOUNDS[params.response].label, can_soothe=True))
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child, role="child", can_make_sound=True))
    guide = world.add(Entity(id="guide", kind="character", type=params.guide_type, label=params.guide, role="guide", can_warn=True, can_soothe=True))
    baby = world.add(Entity(id="baby", kind="character", type="monkey", label="baby monkey", role="baby"))
    trail = world.add(Entity(id="trail", kind="place", type="trail", label="the trail"))

    world.facts["params"] = params
    world.facts["setting"] = SETTINGS[params.setting]
    world.facts["sound"] = SOUNDS[params.sound]
    world.facts["response"] = SOUNDS[params.response]

    _make_story(world)
    return world


SETTINGS = {
    "savanna": Setting(id="savanna", place="the safari savanna", detail="The acacia trees stood like umbrellas, and the dust smelled warm.", sounds=["drum", "chime", "call"]),
    "watering_hole": Setting(id="watering_hole", place="the watering hole", detail="The water flashed like a mirror, and hoofprints ringed the mud.", sounds=["drum", "chime", "call"]),
    "grassland": Setting(id="grassland", place="the grassland", detail="The grass swayed in wide waves, and even the birds seemed to listen.", sounds=["drum", "chime", "call", "whistle"]),
}

SOUNDS = {
    "drum": Sound(id="drum", label="drum", sound="boom-boom", effect="kept the beat", safe=True, volume=2, tags={"music"}),
    "whistle": Sound(id="whistle", label="whistle", sound="tweet-tweet", effect="carried too sharply", safe=False, volume=3, tags={"sharp"}),
    "chime": Sound(id="chime", label="little chime", sound="ting-ting", effect="sparkled through the air", safe=True, volume=1, tags={"music"}),
    "call": Sound(id="call", label="low animal call", sound="oo-oo", effect="answered the open sky", safe=True, volume=1, tags={"music"}),
    "soft_drum": Sound(id="soft_drum", label="soft drum beat", sound="tum-tum", effect="settled everyone down", safe=True, volume=1, tags={"music", "soothe"}),
    "call_and_wait": Sound(id="call_and_wait", label="waiting call", sound="hmm-hmm", effect="asked everyone to pause", safe=True, volume=1, tags={"music", "soothe"}),
}

CURATED = [
    StoryParams(setting="savanna", child="Miri", child_type="monkey", guide="Asha", guide_type="lioness", sound="whistle", response="soft_drum", seed=1),
    StoryParams(setting="grassland", child="Kito", child_type="monkey", guide="Nala", guide_type="lioness", sound="drum", response="call_and_wait", seed=2),
    StoryParams(setting="watering_hole", child="Pema", child_type="monkey", guide="Sefu", guide_type="lion", sound="chime", response="soft_drum", seed=3),
]

GIRL_NAMES = ["Miri", "Nala", "Pema", "Zuri", "Tala"]
BOY_NAMES = ["Kito", "Sefu", "Biko", "Jomo", "Rafi"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS.values():
        for sid, snd in SOUNDS.items():
            for rid, rsp in SOUNDS.items():
                if sound_is_reasonable(snd, setting) and rsp.safe:
                    combos.append((setting.id, sid, rid))
    return combos


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a fable-like safari story for a young child that includes the word "safari" and the sound "{world.facts["sound"].sound}".',
        f"Tell a short animal story where {p.child} chooses a kinder sound on safari after {p.guide} gives wise advice.",
        f'Write a gentle moral story about a safari trail, a loud sound, and a better rhythm that helps everyone stay calm.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    p = world.facts["params"]
    child = p.child
    guide = p.guide
    sound = world.facts["sound"]
    response = world.facts["response"]
    return [
        ("Who is the story about?",
         f"It is about {child} and {guide} on a safari path. {guide} helps the story move from a risky sound to a wiser one."),
        ("What sound did the child want to make?",
         f"{child} wanted to make {sound.label} sounds. The sound was exciting, but not every sound is kind in a quiet animal place."),
        ("How did the problem get solved?",
         f"They chose {response.label} instead. That gentler sound helped everyone stay calm and proved that a wiser choice can still be strong."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    qas = []
    qas.append(("What is a safari?",
                 "A safari is a trip to watch animals in a wild place. People move carefully and listen closely so they do not disturb the animals."))
    qas.append(("Why can a whistle be a bad choice near animals?",
                 "A whistle is sharp and sudden, so it can scare animals. A softer sound is kinder when baby animals are nearby."))
    qas.append(("Why are drums useful in a story like this?",
                 "Drums can make a steady rhythm that helps people move together. A gentle beat can be lively without being frightening."))
    return qas


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
        if e.can_make_sound:
            bits.append("can_make_sound=True")
        if e.can_soothe:
            bits.append("can_soothe=True")
        if e.can_warn:
            bits.append("can_warn=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_sound(S) :- sound(S), safe(S).
reasonable(S, P) :- sound(S), place(P), allowed(P, S), safe(S).
outcome(guided) :- response(soft_drum).
outcome(warned) :- chosen_sound(whistle).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        for snd in s.sounds:
            lines.append(asp.fact("allowed", sid, snd))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        if s.safe:
            lines.append(asp.fact("safe", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    program = asp_program(
        "\n".join([asp.fact("chosen_sound", params.sound), asp.fact("response", params.response)]),
        "#show outcome/1."
    )
    model = asp.one_model(program)
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP parity for valid combos.")
        rc = 1
    else:
        print(f"OK: ASP parity matches valid_combos() ({len(valid_combos())} combos).")
    smoke = generate(CURATED[0])
    if not smoke.story or not smoke.prompts:
        print("SMOKE TEST FAILED: generation produced empty content.")
        rc = 1
    else:
        print("OK: normal generation smoke test passed.")
    if asp_outcome(CURATED[0]) not in {"guided", "warned", "?"}:
        print("SMOKE TEST FAILED: ASP outcome not readable.")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Safari fable story world with sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--response", choices=SOUNDS)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["monkey", "lion", "elephant"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-type", choices=["lion", "lioness", "elephant", "monkey"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.sound is None or c[1] == args.sound)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid safari sound combination matches the given options.)")
    setting, sound, response = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["monkey", "monkey", "elephant", "lion"])
    guide_type = args.guide_type or rng.choice(["lion", "lioness", "elephant"])
    child = args.child or rng.choice(GIRL_NAMES + BOY_NAMES)
    guide = args.guide or rng.choice(["Asha", "Nala", "Sefu", "Kito", "Pema"])
    if args.sound and not SOUNDS[args.sound].safe:
        raise StoryError(f"(Refusing sound '{args.sound}': it is too sharp for this fable.)")
    return StoryParams(setting=setting, child=child, child_type=child_type,
                       guide=guide, guide_type=guide_type, sound=sound,
                       response=response)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.sound not in SOUNDS:
        raise StoryError(f"Unknown sound: {params.sound}")
    if params.response not in SOUNDS:
        raise StoryError(f"Unknown response sound: {params.response}")

    world = World()
    world.add(Entity(id="setting", kind="place", type="place", label=SETTINGS[params.setting].place))
    world.add(Entity(id="sound", kind="thing", type="sound", label=SOUNDS[params.sound].label, can_make_sound=True))
    world.add(Entity(id="response", kind="thing", type="sound", label=SOUNDS[params.response].label, can_soothe=True))
    world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child, role="child", can_make_sound=True))
    world.add(Entity(id="guide", kind="character", type=params.guide_type, label=params.guide, role="guide", can_warn=True, can_soothe=True))
    world.add(Entity(id="baby", kind="character", type="monkey", label="baby monkey", role="baby"))
    world.add(Entity(id="trail", kind="place", type="trail", label="the safari trail"))
    world.facts["params"] = params
    world.facts["setting_obj"] = SETTINGS[params.setting]
    world.facts["sound_obj"] = SOUNDS[params.sound]
    world.facts["response_obj"] = SOUNDS[params.response]
    _make_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show reasonable/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} reasonable (setting, sound) pairs:")
        for setting, sound in combos[:]:
            print(f"  {setting:14} {sound}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and {p.guide}: safari sound fable ({p.setting})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
