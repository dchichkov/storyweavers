#!/usr/bin/env python3
"""
storyworlds/worlds/solid_trumpet_copper_sound_effects_cautionary_fable.py
=========================================================================

A small cautionary fable world about a shiny copper trumpet, a solid little
plan, and the noisy trouble that follows when a character ignores a warning.

The story model keeps a few typed entities with physical meters and emotional
memes. A sound-spread rule turns loud trumpet playing into attention, alarm,
and consequence. The prose is driven by world state, not by a frozen template.

The required seed words appear as world facts and in the rendered tale:
solid, trumpet, copper.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SOUND_MIN = 1.0
WARNING_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str | None = None
    caretaker: str | None = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "doe", "hen"}
        male = {"boy", "father", "dad", "man", "fox", "crow", "wolf", "goat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
            "traits": list(v.traits), "role": v.role, "owner": v.owner, "caretaker": v.caretaker,
            "plural": v.plural, "tags": set(v.tags), "attrs": dict(v.attrs),
            "meters": defaultdict(float, dict(v.meters)), "memes": defaultdict(float, dict(v.memes)),
        }) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.history = [dict(item) for item in self.history]
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


@dataclass
class Setting:
    place: str
    surface: str
    witnesses: list[str] = field(default_factory=list)


@dataclass
class Sound:
    id: str
    label: str
    effect: str
    volume: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Trumpet:
    id: str
    phrase: str
    material: str
    shine: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Warning:
    id: str
    line: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    character: str
    trumpet: str
    warning: str
    sound: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Setting(place="the meadow", surface="soft grass", witnesses=["sparrows", "daisies"]),
    "court": Setting(place="the village court", surface="wide stones", witnesses=["neighbors", "pigeons"]),
    "bridge": Setting(place="the old bridge", surface="solid boards", witnesses=["river reeds", "fish"]),
}

CHARACTERS = {
    "fox": Entity(id="fox", kind="character", type="fox", label="Fox", traits=["clever", "proud"]),
    "hare": Entity(id="hare", kind="character", type="boy", label="Hare", traits=["quick", "curious"]),
    "goat": Entity(id="goat", kind="character", type="goat", label="Goat", traits=["steady", "careful"]),
}

TRUMPETS = {
    "copper": Trumpet(id="copper", phrase="a copper trumpet", material="copper", shine="gleamed like a small sun", tags={"copper", "trumpet", "solid"}),
    "bright": Trumpet(id="bright", phrase="a bright trumpet", material="copper", shine="shone with a warm glow", tags={"trumpet"}),
}

WARNINGS = {
    "hush": Warning(id="hush", line="Keep your trumpet for the parade, not the sleeping lane", lesson="loudness can wake trouble", tags={"lesson", "warning"}),
    "hive": Warning(id="hive", line="Do not toot near the hive", lesson="noise can scatter a whole nest", tags={"lesson", "warning"}),
}

SOUNDS = {
    "toot": Sound(id="toot", label="toot", effect="toot-toot", volume=2, tags={"sound"}),
    "blast": Sound(id="blast", label="blast", effect="BWAAAH!", volume=3, tags={"sound"}),
    "tap": Sound(id="tap", label="tap", effect="tip-tap", volume=1, tags={"sound"}),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ivy", "Tessa"]
BOY_NAMES = ["Pip", "Ben", "Ollie", "Finn", "Jasper"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for s in SETTINGS:
        for c in CHARACTERS:
            for t in TRUMPETS:
                for w in WARNINGS:
                    if t == "copper":
                        combos.append((s, c, t, w))
    return combos


def sound_risk(sound: Sound, trumpet: Trumpet) -> bool:
    return sound.volume >= 1 and trumpet.material == "copper"


def reasonableness_check(params: StoryParams) -> None:
    if params.setting not in SETTINGS or params.character not in CHARACTERS:
        raise StoryError("Unknown setting or character.")
    if params.trumpet not in TRUMPETS or params.warning not in WARNINGS or params.sound not in SOUNDS:
        raise StoryError("Unknown trumpet, warning, or sound.")
    if not sound_risk(SOUNDS[params.sound], TRUMPETS[params.trumpet]):
        raise StoryError("This story needs a loud copper trumpet to make the warning matter.")


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    player = world.get("player")
    if player.meters["sound"] < SOUND_MIN:
        return out
    if ("alarm",) in world.fired:
        return out
    world.fired.add(("alarm",))
    watcher = world.get("watcher")
    watcher.memes["startle"] += 1
    watcher.memes["worry"] += 1
    world.get("crowd").memes["alarm"] += 1
    out.append("__alarm__")
    return out


CAUSAL_RULES = [
    Rule("alarm", "social", _r_alarm),
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


def tell(setting: Setting, character_name: str, character_type: str, trumpet: Trumpet,
         warning: Warning, sound: Sound, cautious_name: str = "Milo",
         cautious_type: str = "boy") -> World:
    world = World()
    player = world.add(Entity(id="player", kind="character", type=character_type, label=character_name, traits=["proud"], role="player"))
    watcher = world.add(Entity(id="watcher", kind="character", type=cautious_type, label=cautious_name, traits=["careful"], role="watcher"))
    crowd = world.add(Entity(id="crowd", kind="character", type="thing", label="the crowd", plural=True, role="crowd"))
    prop = world.add(Entity(id="trumpet", kind="thing", type="thing", label="trumpet", phrase=trumpet.phrase, tags=set(trumpet.tags), attrs={"material": trumpet.material, "shine": trumpet.shine}))
    lane = world.add(Entity(id="lane", kind="thing", type="thing", label=setting.place, phrase=setting.surface, tags={"solid"}, attrs={"surface": setting.surface}))
    world.facts["setting"] = setting.place
    world.facts["witnesses"] = list(setting.witnesses)
    world.facts["warning"] = warning
    world.facts["sound"] = sound
    world.facts["trumpet"] = trumpet
    world.facts["player_name"] = character_name
    world.facts["watcher_name"] = cautious_name

    player.meters["sound"] = 0.0
    watcher.memes["worry"] = 0.0
    world.say(f"{character_name} found {trumpet.phrase} beside {setting.place}, and it {trumpet.shine}.")
    world.say(f"{setting.place.capitalize()} looked {setting.surface}, and the little trumpet felt clever in {character_name}'s hands.")
    world.para()
    world.say(f'Before the first note, {cautious_name} said, "{warning.line}."')
    player.memes["pride"] += 1
    player.meters["sound"] += sound.volume
    world.say(f'But {character_name} lifted the trumpet anyway: {sound.effect}')
    if setting.witnesses:
        world.say(f"The sparrows, or the neighbors, or the river reeds seemed to hold still and listen.")
    propagate(world, narrate=False)
    if world.get("watcher").memes["worry"] >= WARNING_MIN:
        world.say(f"{cautious_name} flinched and called out again, because {warning.lesson}.")
    world.para()
    if sound.volume >= 2:
        world.say(f"The noise rolled over {setting.place} and woke every ear nearby.")
    else:
        world.say(f"The note stayed small, but it still carried over the stones.")
    world.say(f"{character_name} stopped at last and saw that a little sound can travel farther than a proud heart expects.")
    world.say(f"In the end, the trumpet stayed in the open, and the lesson stayed with {character_name}: {warning.lesson}.")
    world.say(f"The final image was simple: the copper trumpet resting on the solid ground, bright and quiet.")
    world.facts["lesson"] = warning.lesson
    world.facts["outcome"] = "warned"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a child about {f["player_name"]} and a copper trumpet, using the words "solid" and "copper".',
        f"Tell a cautionary story where a loud trumpet note teaches {f['player_name']} to listen to a warning.",
        f'Write a fable with sound effects and a clear lesson about {f["player_name"]} blowing a trumpet in {f["setting"]}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    warning: Warning = f["warning"]
    return [
        QAItem(
            question=f"What did {f['player_name']} find beside {f['setting']}?",
            answer=f"{f['player_name']} found a copper trumpet. It was shiny and looked tempting, but it also needed care because loud noise can cause trouble.",
        ),
        QAItem(
            question=f"Why did {f['watcher_name']} tell {f['player_name']} to stop?",
            answer=f"{f['watcher_name']} knew the trumpet could make a loud blast. That warning mattered because noise can travel far and wake up more than one listener.",
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer=f"It taught that loudness can wake trouble, so it is better to listen before sounding a trumpet. The warning turned the ending into a calm one instead of a messy one.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is copper?",
            answer="Copper is a reddish metal. People can make bright, solid things from it, like a trumpet or a pot.",
        ),
        QAItem(
            question="What does a trumpet do?",
            answer="A trumpet makes a strong sound when someone blows into it. Its note can be loud enough to carry across a field.",
        ),
        QAItem(
            question="Why is a solid ground useful in a fable?",
            answer="A solid ground gives a clear, steady place to stand. In stories, it often helps show that a careful choice is more stable than a rushed one.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
    lines.append(f"history={world.history}")
    return "\n".join(lines)


ASP_RULES = r"""
sound_alarm :- player_sound(P), P >= 1.
warning_matters :- sound_alarm.
valid_combo(S,C,T,W) :- setting(S), character(C), trumpet(T), warning(W), trumpet_copper(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CHARACTERS:
        lines.append(asp.fact("character", c))
    for t in TRUMPETS:
        lines.append(asp.fact("trumpet", t))
        if t == "copper":
            lines.append(asp.fact("trumpet_copper", t))
    for w in WARNINGS:
        lines.append(asp.fact("warning", w))
    for snd in SOUNDS:
        lines.append(asp.fact("sound", snd))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_combo/4."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    ok = True
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        ok = False
        print("MISMATCH in valid_combos")
        print("only python:", sorted(py - cl))
        print("only clingo:", sorted(cl - py))
    try:
        sample = generate(StoryParams(setting="meadow", character="fox", trumpet="copper", warning="hive", sound="toot"))
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print(f"OK: ASP parity and smoke test passed ({len(py)} combos).")
        return 0
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, c, t, w) for s in SETTINGS for c in CHARACTERS for t in TRUMPETS if t == "copper" for w in WARNINGS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny cautionary fable world with trumpet sounds and a copper lesson.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--character", choices=CHARACTERS)
    ap.add_argument("--trumpet", choices=TRUMPETS)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--name")
    ap.add_argument("--watcher")
    ap.add_argument("-n", "--n", type=int, default=1)
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
              and (args.character is None or c[1] == args.character)
              and (args.trumpet is None or c[2] == args.trumpet)
              and (args.warning is None or c[3] == args.warning)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, character, trumpet, warning = rng.choice(sorted(combos))
    sound = args.sound or rng.choice(sorted(SOUNDS))
    return StoryParams(setting=setting, character=character, trumpet=trumpet, warning=warning, sound=sound, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.character not in CHARACTERS or params.trumpet not in TRUMPETS or params.warning not in WARNINGS or params.sound not in SOUNDS:
        raise StoryError("Unknown parameter.")
    reasonableness_check(params)
    setting = SETTINGS[params.setting]
    char = CHARACTERS[params.character]
    trumpet = TRUMPETS[params.trumpet]
    warning = WARNINGS[params.warning]
    sound = SOUNDS[params.sound]
    name = params.character.capitalize()
    watcher_name = "Milo"
    if params.character == "fox":
        name = "Fenn"
    elif params.character == "hare":
        name = "Pip"
    elif params.character == "goat":
        name = "Glen"
    world = tell(setting, name, char.type, trumpet, warning, sound, cautious_name=watcher_name)
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
        print(asp_program("#show valid_combo/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(setting=s, character=c, trumpet=t, warning=w, sound="toot")) for s, c, t, w in valid_combos()[:5]]
    else:
        seen: set[str] = set()
        while len(samples) < args.n:
            params = resolve_params(args, rng)
            params.seed = args.seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
