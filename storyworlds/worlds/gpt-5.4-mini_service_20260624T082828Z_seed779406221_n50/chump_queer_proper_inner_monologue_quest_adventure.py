#!/usr/bin/env python3
"""
Storyworld: chump_queer_proper_inner_monologue_quest_adventure

A small adventure-style story world about a little chump who goes on a quest,
talks to himself in an inner monologue, and learns that a proper plan can beat
a queer little problem.

Premise:
- A child-like adventurer wants to finish a quest.
- The quest begins with a proper map or proper tool.
- A queer obstacle makes the route confusing.
- The chump's inner monologue starts doubtful, then grows brave.
- The ending proves the quest changed the world state: the goal is found, the
  mood is steadier, and the proper item is used well.

This script follows the Storyweavers world contract:
- standalone stdlib script
- StoryParams plus CLI support
- world model with meters and memes
- inline ASP twin and Python reasonableness gate
- story, prompts, story QA, world QA, verify/trace/json output
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "chump"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    search: str
    stumble: str
    clue: str
    trouble: str
    theme: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    id: str
    label: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "old_gate": Setting(place="the old gate", affords={"map", "lantern"}),
    "green_hill": Setting(place="the green hill", affords={"map", "rope", "lantern"}),
    "hedge": Setting(place="the hedge path", affords={"map", "lantern", "key"}),
    "harbor": Setting(place="the harbor walk", affords={"lantern", "rope"}),
}

QUESTS = {
    "map": Quest(
        id="map",
        goal="find the proper map",
        search="look for the map",
        stumble="run toward the wrong turn",
        clue="the map points to the west stone",
        trouble="queer twist in the path",
        theme="quest",
        keyword="quest",
        tags={"quest", "map"},
    ),
    "lantern": Quest(
        id="lantern",
        goal="bring back the proper lantern",
        search="look for the lantern",
        stumble="run toward the dark bend",
        clue="the lantern glows near the mossy rail",
        trouble="queer little shadow under the bridge",
        theme="adventure",
        keyword="adventure",
        tags={"quest", "lantern"},
    ),
    "key": Quest(
        id="key",
        goal="find the proper key",
        search="look for the key",
        stumble="dash toward the wrong door",
        clue="the key jingles beside the blue stone",
        trouble="queer narrow gap in the hedge",
        theme="quest",
        keyword="quest",
        tags={"quest", "key"},
    ),
    "rope": Quest(
        id="rope",
        goal="carry back the proper rope",
        search="look for the rope",
        stumble="scramble toward the steep edge",
        clue="the rope hangs by the gate hook",
        trouble="queer sway in the boards",
        theme="adventure",
        keyword="adventure",
        tags={"quest", "rope"},
    ),
}

PRIZES = {
    "map": Prize(label="map", phrase="a proper map", type="map", location="hand"),
    "lantern": Prize(label="lantern", phrase="a small lantern", type="lantern", location="hand"),
    "key": Prize(label="key", phrase="a brass key", type="key", location="pocket"),
    "rope": Prize(label="rope", phrase="a sturdy rope", type="rope", location="shoulder"),
}

TOOLS = [
    Tool(id="lantern", label="the lantern", guards={"dark"}, covers={"hand"}, prep="take the lantern along", tail="carried the lantern carefully"),
    Tool(id="map", label="the map", guards={"lost"}, covers={"hand"}, prep="fold the map neatly", tail="kept the map open"),
    Tool(id="rope", label="the rope", guards={"fall"}, covers={"shoulder"}, prep="tie on the rope", tail="held the rope tight"),
]

NAMES_BOY = ["Pip", "Milo", "Tobin", "Theo", "Joss"]
NAMES_GIRL = ["Ada", "Mina", "Luna", "Nell", "Tia"]
TRAITS = ["brave", "curious", "proper", "quick", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            for prize_id, prize in PRIZES.items():
                if quest_at_risk(QUESTS[qid], prize) and select_tool(QUESTS[qid], prize):
                    out.append((place, qid, prize_id))
    return out


def quest_at_risk(quest: Quest, prize: Prize) -> bool:
    if prize.location == "hand":
        return quest.id in {"map", "lantern"}
    if prize.location == "pocket":
        return quest.id in {"key", "map"}
    return True


def select_tool(quest: Quest, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if prize.location in tool.covers:
            return tool
    return None


def explain_rejection(quest: Quest, prize: Prize) -> str:
    return (
        f"(No story: this quest does not honestly threaten {prize.phrase}. "
        f"The hero needs a real risk and a real fix, so this pairing is refused.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: try a {ok} hero with {PRIZES[prize_id].label}; {gender} is not accepted here.)"


def predict_mess(world: World, hero: Entity, quest: Quest, prize_id: str) -> dict:
    sim = world.copy()
    hero2 = sim.get(hero.id)
    hero2.memes["worry"] += 1
    hero2.memes["desire"] += 1
    sim.facts["went"] = True
    return {"lost": quest.id in {"map", "key"}, "worry": hero2.memes["worry"]}


def _do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    hero.memes["courage"] += 1
    hero.meters[quest.id] = hero.meters.get(quest.id, 0) + 1
    if narrate:
        world.say(f"{hero.id} stepped forward and began the quest.")


def introduce(world: World, hero: Entity, prize: Entity, quest: Quest, parent: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who had a very proper wish: to finish "
        f"a {quest.theme} and bring home {prize.phrase}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} kept a quiet inner monologue, saying, "
        f"\"I may be a chump, but I can still do this carefully.\""
    )


def setup(world: World, hero: Entity, prize: Entity, sidekick: Entity) -> None:
    hero.memes["love"] += 1
    sidekick.memes["trust"] += 1
    world.say(
        f"{hero.id}'s {sidekick.type} friend came along with a proper grin, and "
        f"{hero.id} held {hero.pronoun('possessive')} {prize.label} close."
    )


def enter_setting(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"At {world.setting.place}, the air felt open and ready, but the path had a "
        f"queer little turn that made even a brave step feel strange."
    )
    world.say(
        f"\"{quest.clue},\" {hero.id} thought. \"If I stay proper, I will not get lost.\""
    )


def start_tension(world: World, hero: Entity, prize: Entity, quest: Quest) -> None:
    hero.memes["worry"] += 1
    pred = predict_mess(world, hero, quest, prize.id)
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"{hero.id} wanted to {quest.search}, but {hero.pronoun('possessive')} chest fluttered. "
        f"\"I feel like a chump,\" {hero.id} whispered inside {hero.pronoun('object')} own head."
    )
    world.say(
        f"Still, the queer little problem ahead looked like it could be solved with a proper plan."
    )


def stumble(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["confusion"] += 1
    world.say(
        f"{hero.id} nearly {quest.stumble}, then stopped and listened to the quiet clue."
    )


def reveal_tool(world: World, hero: Entity, prize: Entity, quest: Quest) -> Optional[Tool]:
    tool = select_tool(quest, prize)
    if tool is None:
        return None
    world.say(
        f"Then {hero.id} spotted {tool.label}. That was proper luck, and it gave "
        f"{hero.pronoun('possessive')} mind something steady to hold."
    )
    return tool


def accept_help(world: World, hero: Entity, sidekick: Entity, tool: Tool) -> None:
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0
    world.say(
        f"\"We can do it properly,\" {sidekick.id} said. {hero.id} nodded, took a breath, "
        f"and let the inner monologue turn brave instead of small."
    )
    world.say(
        f"{hero.id} chose to {tool.prep}, and the quest felt less queer and more clear."
    )


def finish(world: World, hero: Entity, quest: Quest, prize: Entity, tool: Tool) -> None:
    hero.memes["pride"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"At last, {hero.id} found {prize.phrase}. {tool.tail}, and the proper prize was "
        f"safe at {hero.pronoun('possessive')} side."
    )
    world.say(
        f"{hero.id} smiled to {hero.pronoun('object')}self and thought, "
        f"\"A chump can become a quest-finder when {hero.pronoun('subject')} keeps going.\""
    )


def tell(setting: Setting, quest: Quest, prize_cfg: Prize,
         hero_name: str = "Pip", hero_type: str = "boy",
         sidekick_type: str = "friend", hero_trait: str = "proper") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    sidekick = world.add(Entity(id="Sidekick", kind="character", type=sidekick_type))
    parent = world.add(Entity(id="Guide", kind="character", type="guide", label="the guide"))
    prize = world.add(Entity(
        id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, plural=prize_cfg.plural
    ))
    introduce(world, hero, prize, quest, parent)
    world.para()
    setup(world, hero, prize, sidekick)
    enter_setting(world, hero, quest)
    start_tension(world, hero, prize, quest)
    stumble(world, hero, quest)
    tool = reveal_tool(world, hero, prize, quest)
    if tool is None:
        raise StoryError("No proper tool can resolve this quest.")
    accept_help(world, hero, sidekick, tool)
    world.para()
    finish(world, hero, quest, prize, tool)
    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        parent=parent,
        prize=prize,
        quest=quest,
        tool=tool,
        resolved=True,
        trait=hero_trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prize, quest = f["hero"], f["prize"], f["quest"]
    return [
        f'Write a short adventure story for a young child about a chump on a {quest.keyword} quest.',
        f"Tell a gentle story where {hero.id} keeps an inner monologue, feels like a chump, and still uses a proper tool to finish {quest.goal}.",
        f"Write a quest story that includes the words 'chump', 'queer', and 'proper' in a child-friendly way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prize, quest = f["hero"], f["prize"], f["quest"]
    sidekick = f["sidekick"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type} who goes on a {quest.theme} and brings home {prize.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {quest.search} and finish the quest in a proper way.",
        ),
        QAItem(
            question=f"How did the inner monologue help {hero.id}?",
            answer=f"The inner monologue let {hero.id} speak quietly to {hero.pronoun('object')}self, calm the worry, and keep going instead of stopping like a chump.",
        ),
        QAItem(
            question=f"Who helped {hero.id} on the quest?",
            answer=f"{sidekick.id} helped by encouraging {hero.id} to stay proper and use the right tool.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"At the end, {hero.id} had {prize.phrase}, the quest was finished, and the queer problem had become a clear one.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task where someone goes looking for something important and tries to solve a problem along the way.",
        )
    ],
    "map": [
        QAItem(
            question="What does a map do?",
            answer="A map shows where places are and can help someone find the right path.",
        )
    ],
    "lantern": [
        QAItem(
            question="What is a lantern for?",
            answer="A lantern gives light so people can see better in the dark.",
        )
    ],
    "key": [
        QAItem(
            question="What does a key do?",
            answer="A key opens a lock when it matches the right shape.",
        )
    ],
    "rope": [
        QAItem(
            question="What is rope used for?",
            answer="Rope can help someone carry, tie, or hold things more safely.",
        )
    ],
    "proper": [
        QAItem(
            question="What does proper mean?",
            answer="Proper means done in the right, careful, or suitable way.",
        )
    ],
    "queer": [
        QAItem(
            question="What does queer mean in this story?",
            answer="Here, queer means strange or unusual, not normal or expected.",
        )
    ],
    "chump": [
        QAItem(
            question="What does chump mean here?",
            answer="Here, chump means a lovable, clumsy fellow who feels unsure but can still do the job.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags)
    tags.update({"proper", "queer", "chump"})
    out: list[QAItem] = []
    for tag in ["quest", "map", "lantern", "key", "rope", "proper", "queer", "chump"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hedge", quest="map", prize="map", name="Pip", gender="boy", sidekick="friend", trait="proper"),
    StoryParams(place="old_gate", quest="lantern", prize="lantern", name="Ada", gender="girl", sidekick="friend", trait="curious"),
    StoryParams(place="green_hill", quest="rope", prize="rope", name="Milo", gender="boy", sidekick="friend", trait="brave"),
    StoryParams(place="hedge", quest="key", prize="key", name="Nell", gender="girl", sidekick="friend", trait="gentle"),
]


ASP_RULES = r"""
quest_risk(Q,P) :- quest(Q), prize(P), risk_on(Q, L), prize_at(P, L).
proper_fix(Q,P,T) :- quest_risk(Q,P), tool(T), covers(T, L), prize_at(P, L).
valid_story(Place,Q,P,G) :- affords(Place,Q), quest_risk(Q,P), proper_fix(Q,P,_), wears(G,P).
valid_combo(Place,Q,P) :- affords(Place,Q), quest_risk(Q,P), proper_fix(Q,P,_).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("risk_on", qid, qid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_at", pid, p.location))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def valid_asp_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(valid_asp_combos())
    if asp_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if asp_set - python_set:
        print(" only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print(" only in python:", sorted(python_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: chump, queer, proper, quest, and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sidekick", default="friend")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.quest and args.prize:
        q, p = QUESTS[args.quest], PRIZES[args.prize]
        if not (quest_at_risk(q, p) and select_tool(q, p)):
            raise StoryError(explain_rejection(q, p))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.quest is None or c[1] == args.quest)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest_id, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest_id, prize=prize_id, name=name, gender=gender, sidekick=args.sidekick, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], PRIZES[params.prize],
                 params.name, params.gender, params.sidekick, params.trait)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = valid_asp_combos()
        stories = valid_asp_stories()
        print(f"{len(triples)} compatible (place, quest, prize) combos ({len(stories)} with gender):\n")
        for place, q, p in triples:
            print(f"  {place:10} {q:8} {p:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.quest} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
