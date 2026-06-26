#!/usr/bin/env python3
"""
A standalone storyworld for a tiny fairy-tale domain about a choice in a bog,
a moral value, and a quest.

The tale premise:
- A small hero must choose whether to take a glittering shortcut through a bog
  or keep a promise and follow the longer safe path.
- A lost treasure or helper is tied to the hero's moral choice.
- The quest resolves when the hero makes the kinder, wiser choice and earns
  a fairytale ending image.

This script follows the Storyweavers world contract: it defines the per-world
params, a simulated world model with meters and memes, a reasonableness gate,
an inline ASP twin, QA generation, and a CLI.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


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
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "woman"}
        male = {"boy", "king", "prince", "man"}
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
    mood: str
    has_bog: bool = True
    affordance: str = "quest"


@dataclass
class Quest:
    id: str
    goal: str
    motive: str
    danger: str
    route: str
    shortcut: str
    reward: str
    kind_word: str = "quest"
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralValue:
    id: str
    value_word: str
    temptation: str
    better_choice: str
    cost: str
    blessing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    choice_made: str = ""
    bog_state: str = "quiet"
    treasure_saved: bool = False
    moral_resolved: bool = False

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.choice_made = self.choice_made
        clone.bog_state = self.bog_state
        clone.treasure_saved = self.treasure_saved
        clone.moral_resolved = self.moral_resolved
        clone.facts = dict(self.facts)
        return clone


def _r_bog_sink(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters.get("bog_step", 0.0) < THRESHOLD:
        return out
    if world.choice_made == "shortcut" and ("sink", hero.id) not in world.fired:
        world.fired.add(("sink", hero.id))
        hero.meters["mud"] = hero.meters.get("mud", 0.0) + 1.0
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
        world.bog_state = "swallowed"
        out.append("The bog caught at the hero's shoes and splashed cold mud up the hem.")
    return out


def _r_truth_blossom(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not hero or not helper:
        return out
    if world.choice_made != "kind" or ("blossom", hero.id) in world.fired:
        return out
    if hero.memes.get("courage", 0.0) >= THRESHOLD and hero.memes.get("kindness", 0.0) >= THRESHOLD:
        world.fired.add(("blossom", hero.id))
        hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1.0
        helper.memes["hope"] = helper.memes.get("hope", 0.0) + 1.0
        world.moral_resolved = True
        out.append("A warm light seemed to rise from the lily pads, as if the bog itself approved.")
    return out


CAUSAL_RULES = [
    _r_bog_sink,
    _r_truth_blossom,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(quest: Quest, moral: MoralValue) -> bool:
    return bool(quest.shortcut) and bool(quest.danger) and bool(moral.temptation) and bool(moral.better_choice)


def predict_outcome(world: World, choice: str) -> dict:
    sim = world.copy()
    sim.choice_made = choice
    hero = sim.get("hero")
    if choice == "shortcut":
        hero.meters["bog_step"] = hero.meters.get("bog_step", 0.0) + 1.0
    else:
        hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1.0
        hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    propagate(sim, narrate=False)
    return {
        "mud": hero.meters.get("mud", 0.0),
        "peace": hero.memes.get("peace", 0.0),
        "resolved": sim.moral_resolved,
    }


SETTINGS = {
    "lantern_hollow": Setting(name="Lantern Hollow", mood="golden"),
    "silver_wood": Setting(name="Silver Wood", mood="quiet"),
    "mossy_gate": Setting(name="Mossy Gate", mood="misty"),
}

QUESTS = {
    "moss_crown": Quest(
        id="moss_crown",
        goal="bring back the moss crown",
        motive="save the old brook spirit",
        danger="the bog is full of sinking roots",
        route="the long stone path",
        shortcut="the slimy bog path",
        reward="a blessing from the brook spirit",
        tags={"quest", "bog"},
    ),
    "star_lily": Quest(
        id="star_lily",
        goal="find the star lily",
        motive="heal a tired grandmother",
        danger="the bog mirrors tricks in the water",
        route="the willow road",
        shortcut="the reed-choked bog",
        reward="a lantern that never goes dim",
        tags={"quest", "bog"},
    ),
    "lost_harp": Quest(
        id="lost_harp",
        goal="return the lost harp",
        motive="help the singing knight keep a promise",
        danger="the bog whispers wrong turns",
        route="the dry ridge",
        shortcut="the mud-thread trail",
        reward="a song of thanks at the castle",
        tags={"quest", "bog"},
    ),
}

MORAL_VALUES = {
    "promise": MoralValue(
        id="promise",
        value_word="keeping a promise",
        temptation="the quick path looks easier",
        better_choice="taking the honest, safe road",
        cost="a few extra steps",
        blessing="trust grows stronger",
        tags={"moral", "value"},
    ),
    "kindness": MoralValue(
        id="kindness",
        value_word="kindness",
        temptation="the hero can hurry past a small cry for help",
        better_choice="stopping to help first",
        cost="a little time",
        blessing="a lonely friend feels seen",
        tags={"moral", "value"},
    ),
    "honesty": MoralValue(
        id="honesty",
        value_word="honesty",
        temptation="the shiny reeds invite a sneaky shortcut",
        better_choice="telling the truth about the lost treasure",
        cost="a careful confession",
        blessing="the way home becomes clear",
        tags={"moral", "value"},
    ),
}

HERO_NAMES = ["Ella", "Nico", "Mira", "Tobin", "Pippa", "Bram", "Lena", "Jory"]
HELPER_NAMES = ["Turtle", "Moss Mouse", "Old Crane", "Little Lantern"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    moral: str
    name: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a choice in a bog.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--moral", choices=MORAL_VALUES)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    quest = args.quest or rng.choice(sorted(QUESTS))
    moral = args.moral or rng.choice(sorted(MORAL_VALUES))
    if not reasonableness_gate(QUESTS[quest], MORAL_VALUES[moral]):
        raise StoryError("The chosen quest and moral value do not make a fair fairy-tale choice.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, quest=quest, moral=moral, name=name, helper=helper)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    quest = QUESTS[params.quest]
    moral = MORAL_VALUES[params.moral]

    hero = world.add(Entity(id="hero", kind="character", type="girl", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="thing", label=params.helper))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type="thing",
        label=quest.goal.replace("bring back the ", "").replace("find the ", "").replace("return the ", ""),
        phrase=quest.reward,
        owner=hero.id,
        caretaker=helper.id,
        place="bog-edge",
    ))

    world.say(
        f"Once in {world.setting.name}, there was a small traveler named {params.name} "
        f"who had a brave heart and a curious step."
    )
    world.say(
        f"{params.name} had a great {quest.kind_word} to {quest.goal}, because {quest.motive}."
    )
    world.say(
        f"But the way ahead split in two: {quest.route}, or {quest.shortcut}."
    )
    world.para()
    world.say(
        f"The bog glittered with bright beads of water, and it whispered a tricky choice."
    )
    world.say(
        f"{params.name} knew that {moral.value_word} mattered, even when {moral.temptation}."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        treasure=treasure,
        quest=quest,
        moral=moral,
        setting=world.setting,
        params=params,
    )

    choice = "kind"
    predicted_shortcut = predict_outcome(world, "shortcut")
    if predicted_shortcut["mud"] > 0:
        world.say(
            f"{params.helper} pointed at the sinking reeds and said the bog would be cruel to a rushed step."
        )
    world.say(
        f"So {params.name} chose {moral.better_choice} instead of the tempting short path."
    )
    world.choice_made = choice
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1.0
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    hero.meters["bog_step"] = 0.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"At last, {params.name} reached the end of the route and found {quest.reward} waiting like a little sunrise."
    )
    world.say(
        f"The treasure stayed safe, and the bog no longer seemed frightful; it was only a wet place that had been met with wisdom."
    )

    world.treasure_saved = True
    world.moral_resolved = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    q = world.facts["quest"]
    m = world.facts["moral"]
    return [
        f'Write a short fairy tale for a child about {p.name}, a bog, and a hard choice.',
        f"Tell a gentle quest story where {p.name} must decide between {q.route} and {q.shortcut}, while remembering {m.value_word}.",
        f'Write a simple story that includes a moral value, a quest, and the word "bog".',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    q = world.facts["quest"]
    m = world.facts["moral"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"What choice did {p.name} make in the story?",
            answer=f"{p.name} chose {m.better_choice.lower()} instead of the tempting shortcut through the bog.",
        ),
        QAItem(
            question=f"Why was the quest hard for {p.name}?",
            answer=f"The quest was hard because {q.danger}, so the shortcut looked easy but risky.",
        ),
        QAItem(
            question=f"Who helped {p.name} notice the wise path?",
            answer=f"{helper.label} helped by pointing out the bog's danger and reminding {p.name} to stay true to {m.value_word}.",
        ),
        QAItem(
            question=f"What happened to the treasure at the end?",
            answer=f"The treasure was saved, and {q.reward.lower()} came with the good choice.",
        ),
        QAItem(
            question=f"How did {p.name} show a good moral value?",
            answer=f"{hero.label} showed {m.value_word} by choosing the safer road and doing what was right even when the shortcut tempted {hero.label.lower()}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bog?",
            answer="A bog is a wet, muddy place where the ground can be soft and tricky to walk on.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or mission where someone goes looking for something important.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way of acting, like kindness, honesty, or keeping a promise.",
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
    lines.append(f"setting={world.setting.name}, mood={world.setting.mood}, bog_state={world.bog_state}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"choice_made={world.choice_made}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A quest can be reasoned about declaratively.
quest_ok(Q) :- quest(Q), goal(Q,_), danger(Q,_), route(Q,_), shortcut(Q,_).

% A moral choice is reasonable when the virtue has a clear temptation and a better choice.
moral_ok(M) :- moral(M), temptation(M,_), better_choice(M,_).

% The story is valid when quest and moral can pair.
valid_story(S, Q, M) :- setting(S), quest_ok(Q), moral_ok(M), bog_setting(S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_bog:
            lines.append(asp.fact("bog_setting", sid))
        lines.append(asp.fact("mood", sid, s.mood))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("goal", qid, q.goal))
        lines.append(asp.fact("motive", qid, q.motive))
        lines.append(asp.fact("danger", qid, q.danger))
        lines.append(asp.fact("route", qid, q.route))
        lines.append(asp.fact("shortcut", qid, q.shortcut))
    for mid, m in MORAL_VALUES.items():
        lines.append(asp.fact("moral", mid))
        lines.append(asp.fact("temptation", mid, m.temptation))
        lines.append(asp.fact("better_choice", mid, m.better_choice))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(s, q, m) for s in SETTINGS for q in QUESTS for m in MORAL_VALUES
                  if SETTINGS[s].has_bog and reasonableness_gate(QUESTS[q], MORAL_VALUES[m])}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(setting="lantern_hollow", quest="moss_crown", moral="promise", name="Ella", helper="Old Crane"),
    StoryParams(setting="silver_wood", quest="star_lily", moral="kindness", name="Mira", helper="Turtle"),
    StoryParams(setting="mossy_gate", quest="lost_harp", moral="honesty", name="Nico", helper="Little Lantern"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story combinations:\n")
        for s, q, m in stories:
            print(f"  {s:14} {q:12} {m}")
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.quest} / {p.moral} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
