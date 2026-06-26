#!/usr/bin/env python3
"""
storyworlds/worlds/thirteenth_tuba_quest_space_adventure.py
===========================================================

A small space-adventure story world about the thirteenth tuba quest.

Premise:
- A young space courier and a helper robot must carry a tuba to a moon
  festival.
- The tuba is big, shiny, and easy to bump.
- The ship passes through a narrow ring of floating stone and needs a careful
  route.

Story shape:
- Setup: the crew learns what the quest is and why the tuba matters.
- Tension: the tuba drifts, clangs, and risks a bad stumble in zero gravity.
- Turn: the helper finds a safer way to secure the instrument.
- Resolution: they arrive in time, and the tuba becomes the bright sound of the
  thirteenth quest.

The world model tracks:
- meters: position, speed, float, bump, dust, tether, glow, etc.
- memes: worry, pride, teamwork, relief, curiosity, confidence, delight.

The inline ASP twin checks that the reasonable quest routes match the Python
reasonableness gate.
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


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    tethered_to: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str
    kind: str
    route: str
    shining: str
    requires: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    risk: str
    region: str
    needs: set[str] = field(default_factory=set)
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    id: str
    label: str
    action: str
    helps: set[str]
    fits: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.route_clear: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.route_clear = self.route_clear
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "orbital_port": Setting(
        name="the orbital port",
        kind="spaceport",
        route="glass tunnel",
        shining="the station lights glittered on the windows",
        requires={"tether"},
    ),
    "moon_dock": Setting(
        name="the moon dock",
        kind="moonbase",
        route="silver ramp",
        shining="dusty craters glowed under the lamps",
        requires={"tether"},
    ),
    "ring_station": Setting(
        name="the ring station",
        kind="station",
        route="slow spin corridor",
        shining="the corridor lights blinked like tiny stars",
        requires={"tether", "steady"},
    ),
}

QUESTS = {
    "thirteenth_tuba": QuestItem(
        id="thirteenth_tuba",
        label="the thirteenth tuba",
        phrase="a bright brass tuba for the thirteenth quest",
        risk="bang and ding",
        region="cargo",
        needs={"tether"},
        genders={"girl", "boy"},
    ),
    "festival_horn": QuestItem(
        id="festival_horn",
        label="the festival horn",
        phrase="a polished horn for the moon band",
        risk="scratch and rattle",
        region="cargo",
        needs={"tether"},
        genders={"girl", "boy"},
    ),
    "giant_drum": QuestItem(
        id="giant_drum",
        label="the giant drum",
        phrase="a round drum with a moon-white skin",
        risk="bump and thump",
        region="cargo",
        needs={"tether", "steady"},
        genders={"girl", "boy"},
    ),
}

TOOLS = {
    "tether": Tool(
        id="tether",
        label="a soft tether",
        action="clip the instrument to the wall",
        helps={"tether"},
        fits={"cargo"},
    ),
    "foam_cradle": Tool(
        id="foam_cradle",
        label="a foam cradle",
        action="set the instrument into the foam cradle",
        helps={"steady"},
        fits={"cargo"},
    ),
    "mag_clamp": Tool(
        id="mag_clamp",
        label="a magnet clamp",
        action="snap the clamp shut",
        helps={"tether"},
        fits={"cargo"},
    ),
}

NAMES = ["Mina", "Toby", "Zara", "Lio", "Nia", "Pax", "Ivy", "Rune"]
TYPES = {"girl": ["girl", "captain"], "boy": ["boy", "pilot"]}


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    quest: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin facts/rules
# ---------------------------------------------------------------------------
ASP_RULES = r"""
quest_requires(Q, R) :- quest(Q), needs(Q, R).
route_safe(S, Q) :- setting(S), quest(Q), route_capable(S, Q), has_tool(Q, R), quest_requires(Q, R).
valid_story(S, Q, G) :- route_safe(S, Q), wears(G, Q).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for n in sorted(q.needs):
            lines.append(asp.fact("needs", qid, n))
        for g in sorted(q.genders):
            lines.append(asp.fact("wears", g, qid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    # route_capable facts are produced from the Python reasonableness gate
    for sid, s in SETTINGS.items():
        for qid in QUESTS:
            if reason_ok(sid, qid):
                lines.append(asp.fact("route_capable", sid, qid))
                for n in sorted(QUESTS[qid].needs):
                    if n in tool_help_set():
                        lines.append(asp.fact("has_tool", qid, n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def tool_help_set() -> set[str]:
    out: set[str] = set()
    for t in TOOLS.values():
        out |= set(t.helps)
    return out


def reason_ok(setting_id: str, quest_id: str) -> bool:
    setting = SETTINGS[setting_id]
    quest = QUESTS[quest_id]
    return quest.needs.issubset(tool_help_set()) and setting.requires.issubset(tool_help_set())


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for qid in QUESTS:
            if reason_ok(sid, qid):
                combos.append((sid, qid))
    return combos


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def predict_drift(world: World, hero: Entity, quest: QuestItem) -> dict:
    sim = world.copy()
    _start_quest(sim, sim.get(hero.id), quest, narrate=False)
    cargo = sim.get(quest.id)
    return {
        "bump": cargo.meters.get("bump", 0.0),
        "float": cargo.meters.get("float", 0.0),
    }


def _start_quest(world: World, hero: Entity, quest: QuestItem, narrate: bool = True) -> None:
    hero.memes["purpose"] = hero.memes.get("purpose", 0.0) + 1
    cargo = world.get(quest.id)
    cargo.carried_by = hero.id
    cargo.meters["float"] = cargo.meters.get("float", 0.0) + 1
    if world.setting.kind in {"spaceport", "moonbase", "station"}:
        cargo.meters["bump"] = cargo.meters.get("bump", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} took up the {quest.label} for the thirteenth quest.")


def _apply_risk(world: World, hero: Entity, quest: QuestItem) -> None:
    cargo = world.get(quest.id)
    if cargo.carried_by != hero.id:
        return
    if cargo.meters.get("float", 0.0) >= 1 and not world.route_clear:
        sig = ("risk", quest.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        cargo.meters["bump"] = cargo.meters.get("bump", 0.0) + 1
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
        world.say(f"The {quest.label} drifted and tapped the side of the ship.")


def _apply_tool(world: World, tool: Tool, quest: QuestItem) -> None:
    cargo = world.get(quest.id)
    if cargo.meters.get("bump", 0.0) < 1:
        return
    if not tool.helps.issubset(quest.needs | {"tether", "steady"}):
        return
    sig = ("tool", tool.id, quest.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    cargo.meters["bump"] = 0.0
    cargo.meters["steady"] = cargo.meters.get("steady", 0.0) + 1
    world.route_clear = True
    world.say(f"They used {tool.label} and {tool.action}.")


def travel(world: World, hero: Entity, quest: QuestItem) -> None:
    world.say(f"They moved along {world.setting.route}, where {world.setting.shining}.")
    _apply_risk(world, hero, quest)


def resolve(world: World, hero: Entity, quest: QuestItem) -> None:
    cargo = world.get(quest.id)
    tool = TOOLS["tether"] if "tether" in quest.needs else TOOLS["foam_cradle"]
    _apply_tool(world, tool, quest)
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    cargo.meters["float"] = 0.0
    world.say(
        f"At last, the {quest.label} rode safely through the {world.setting.kind}, "
        f"and the thirteenth quest could be finished."
    )


def tell(setting: Setting, quest: QuestItem, name: str, gender: str, helper: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=helper))
    guide = world.add(Entity(id="Guide", kind="character", type="pilot", label="the guide"))
    cargo = world.add(Entity(
        id=quest.id,
        type="thing",
        label=quest.label,
        phrase=quest.phrase,
        caretaker=guide.id,
    ))

    world.say(f"{hero.id} was a {hero.type} on a small space ship with {guide.label}.")
    world.say(f"Their job was the thirteenth tuba quest: carry {quest.phrase} to the moon band.")
    world.para()
    world.say(f"{setting.name} waited ahead, and {setting.shining}.")
    world.say(f"{hero.id} wanted to keep the tuba steady, but the narrow route made every bump feel bigger.")
    _start_quest(world, hero, quest)
    travel(world, hero, quest)
    world.para()
    resolve(world, hero, quest)

    world.facts.update(
        hero=hero,
        guide=guide,
        quest=quest,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short space adventure story for a young child about a thirteenth tuba quest.",
        f"Tell a gentle quest story where {f['hero'].id} must carry {f['quest'].label} through {f['setting'].name}.",
        f"Write a child-friendly story about a space crew, a shiny tuba, and a safer way to cross {f['setting'].route}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    quest: QuestItem = f["quest"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What was the thirteenth quest about?",
            answer=f"It was about carrying {quest.phrase} safely to the moon band.",
        ),
        QAItem(
            question=f"Why did {hero.id} need to be careful on {setting.route}?",
            answer=f"The route was narrow, so the tuba could drift, bump, and make the trip shaky.",
        ),
        QAItem(
            question=f"What helped the tuba stay safe at the end?",
            answer=f"A soft tether helped hold the tuba steady so it could arrive without a bad clang.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the quest was finished?",
            answer=f"{hero.id} felt proud and relieved because the thirteenth tuba quest was complete.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a tether do in space?",
            answer="A tether helps keep something from floating away when gravity is weak.",
        ),
        QAItem(
            question="Why are shiny things easy to notice on a space station?",
            answer="Shiny things catch the light, so they stand out against the dark of space.",
        ),
        QAItem(
            question="What is a tuba?",
            answer="A tuba is a big brass instrument with a deep sound.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  route_clear={world.route_clear}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verify
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="orbital_port", quest="thirteenth_tuba", name="Mina", gender="girl", helper="captain"),
    StoryParams(setting="moon_dock", quest="festival_horn", name="Toby", gender="boy", helper="pilot"),
    StoryParams(setting="ring_station", quest="giant_drum", name="Zara", gender="girl", helper="captain"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world: the thirteenth tuba quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["captain", "pilot"])
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
              and (args.quest is None or c[1] == args.quest)]
    if not combos:
        raise StoryError("(No valid space-quest combination matches the given options.)")
    setting, quest = rng.choice(sorted(combos))
    q = QUESTS[quest]
    gender = args.gender or rng.choice(sorted(q.genders))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(TYPES[gender])
    return StoryParams(setting=setting, quest=quest, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], params.name, params.gender, params.helper)
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


def asp_valid_stories() -> list[tuple]:
    return []


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_combos()
        print(f"{len(combos)} compatible space-quest combos:\n")
        for s, q in combos:
            print(f"  {s:12} {q}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.name}: {p.quest} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
