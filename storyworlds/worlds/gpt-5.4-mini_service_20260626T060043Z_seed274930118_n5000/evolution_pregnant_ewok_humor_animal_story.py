#!/usr/bin/env python3
"""
A small humorous animal-story world about an ewok family, a surprising
pregnancy, and an "evolution" mishap that changes how the creatures behave.

Premise:
- A young ewok wants to be brave, but the forest keeps turning ordinary plans
  into silly little problems.
- A pregnant mother needs comfort, rest, and help with a heavy chore.
- The child learns to help in a new way, which is the story's tiny "evolution":
  a change in behavior, not biology.

The world is state-driven:
- physical meters: hunger, tiredness, wobble, load, laughter, readiness
- emotional memes: worry, care, pride, mischief, relief

Humor comes from concrete, child-facing misunderstandings:
- acorns rolling underfoot
- a too-serious "evolution lesson"
- a stubborn ewok trying to invent a grand solution
- a small practical fix that ends up being funny and kind
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("hunger", "tiredness", "wobble", "load", "readiness", "warmth"):
            self.meters.setdefault(k, 0.0)
        for k in ("worry", "care", "pride", "mischief", "relief", "humor", "love"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Kiri"
    parent_name: str = "Mara"
    companion_name: str = "Pip"
    place: str = "the mossy tree-home"
    activity: str = "carry the berry basket"
    concern: str = "the heavy basket"
    helper: str = "a vine sling"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


def _bump(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] += amount


def _feel(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] += amount


SCENARIOS = [
    {
        "task": "carry a berry basket to the supper table",
        "problem": "the basket handle pinched Mara's hand whenever it tilted",
        "mistake": "balanced it on a springy stick, which launched three berries into Pip's hood",
        "clue": "two broad straps on an old gathering bag spread its weight evenly",
        "plan": "lined the basket with moss and fitted the soft vine sling beneath it",
        "result": "the sling supported the basket while Kiri and Pip carried one end each",
        "joke": "Pip bowed to the berries and asked them to remain seated",
        "ending": "three red berries rested in Pip's hood like a tiny crown",
    },
    {
        "task": "make a quiet nest corner for the coming baby",
        "problem": "a stack of dry leaves crackled loudly whenever anyone crossed the room",
        "mistake": "ordered the leaves to hush, then tried to glare each one into silence",
        "clue": "damp moss under one loose leaf made no crackle at all",
        "plan": "moved the dry leaves outdoors and laid clean springy moss on the floor",
        "result": "the nest corner became soft and quiet without anyone lifting a heavy bundle alone",
        "joke": "Pip whispered that the leaves had been promoted to outdoor musicians",
        "ending": "one last leaf gave a polite little crunch beside the moonlit doorway",
    },
    {
        "task": "bring warm broth from the cooking fire",
        "problem": "the full bowl sloshed whenever the path bent around a root",
        "mistake": "walked stiffly like a tall parade droid and splashed broth onto an empty spoon",
        "clue": "a beetle crossed the root slowly without tipping the seed shell on its back",
        "plan": "used a shallow covered pot and cleared the walking path with Pip",
        "result": "Kiri carried the covered broth while Mara chose a comfortable place to sit",
        "joke": "Pip tasted the empty spoon and declared it perfectly underseasoned",
        "ending": "steam curled from the opened pot while the spotless spoon shone nearby",
    },
    {
        "task": "sort tiny wraps and blankets for the baby",
        "problem": "every folded cloth looked alike in the dim tree-home",
        "mistake": "made a tower taller than Kiri, which leaned over and dressed Pip all at once",
        "clue": "Mara could identify each cloth by its stitched edge and texture",
        "plan": "made low labeled baskets for warm wraps, soft cloths, and washing cloths",
        "result": "Mara could point to what she wanted and the children could fetch it safely",
        "joke": "Pip waddled out of the fallen pile and announced a new blanket fashion",
        "ending": "three tidy baskets sat below a single folded green wrap",
    },
    {
        "task": "repair the footpath to the family garden",
        "problem": "rain had left a slick patch that Mara said she preferred not to cross",
        "mistake": "sprinkled acorn caps over the mud, creating dozens of tiny rolling shoes",
        "clue": "flat bark stayed firm where it rested across two dry stones",
        "plan": "marked the slippery patch and asked the adult path keeper to place a bark walkway",
        "result": "the family used the dry route after the keeper checked every piece",
        "joke": "Pip collected the acorn caps before they could start a shoe shop",
        "ending": "clean pawprints stopped at the edge of the new bark path",
    },
    {
        "task": "hang a welcome mobile above the baby's empty cradle",
        "problem": "the wooden stars bumped together with a clack that startled everyone",
        "mistake": "wrapped every star in socks until the mobile looked like dangling feet",
        "clue": "stars tied at different lengths could turn without colliding",
        "plan": "retied the pieces at staggered heights while Mara watched from her cushion",
        "result": "the mobile turned gently and chimed only when someone touched it",
        "joke": "Pip asked whether the sock-mobile would walk away at bedtime",
        "ending": "a small wooden moon turned silently above the waiting cradle",
    },
    {
        "task": "gather ripe glow-plums before an evening storm",
        "problem": "the best fruit grew beyond the low branches Mara could comfortably reach",
        "mistake": "shook the trunk so grandly that one plum landed with a plop in Kiri's own basket-hat",
        "clue": "a forked gathering pole could twist ripe stems without shaking the tree",
        "plan": "asked Mara which fruit was ripe while Kiri used the pole and Pip held the basket",
        "result": "they gathered enough fruit without climbing or making Mara overreach",
        "joke": "Pip called the plum in Kiri's hat a very fresh idea",
        "ending": "the first raindrop tapped a basket filled with unbruised glowing fruit",
    },
    {
        "task": "find a comfortable way for Mara to join story circle",
        "problem": "the usual stump made Mara's back ache after a few minutes",
        "mistake": "piled up so many cushions that Mara would have needed a ladder",
        "clue": "Mara said one firm cushion behind her back helped more than a tall pile",
        "plan": "listened to her directions and arranged a low seat with one back cushion and a footrest",
        "result": "Mara settled comfortably and chose to stay for the whole tale",
        "joke": "Pip sat on the leftover cushion mountain and slowly disappeared",
        "ending": "the family shared the final page around Mara's low, steady seat",
    },
    {
        "task": "organize the pantry before the baby arrives",
        "problem": "frequently used jars were stored on the highest shelf",
        "mistake": "invented a pulley from spoons, which rang like a dinner bell and lifted nothing",
        "clue": "Mara explained that easy reach mattered more than a clever machine",
        "plan": "asked an adult to move everyday supplies to a waist-high shelf and labeled each row",
        "result": "Mara could reach what she needed without stretching or carrying boxes",
        "joke": "Pip served the useless spoon pulley a formal resignation letter",
        "ending": "labeled jars stood in one bright row above the quiet spoons",
    },
    {
        "task": "prepare a gentle walking game for the family picnic",
        "problem": "Kiri's first course required hopping over roots and racing uphill",
        "mistake": "declared that everyone could simply grow longer legs by lunchtime",
        "clue": "Mara said she wanted to join but needed a level route and chances to rest",
        "plan": "redrew the game as a clue walk with benches, shade, and no time limit",
        "result": "everyone played at a comfortable pace and Mara chose when to pause",
        "joke": "Pip measured both legs twice and reported no lunchtime growth",
        "ending": "the final clue waited beneath a shady bench beside four muddy footprints",
    },
    {
        "task": "carry clean water to the washing basin",
        "problem": "one large bucket was awkward and heavier than Mara wanted to carry",
        "mistake": "filled a leaf boat, which sailed in a proud circle and soaked Kiri's toes",
        "clue": "two small covered flasks were easier to hold and did not slosh",
        "plan": "made several short trips with Pip using the covered flasks",
        "result": "the basin filled while Mara rested and checked that the water was comfortably warm",
        "joke": "Pip named the escaped leaf boat Admiral Drippy",
        "ending": "two empty flasks dried beside a basin rippling in the firelight",
    },
    {
        "task": "plan the watch schedule for the night before the baby's due date",
        "problem": "Kiri volunteered for every watch and became too sleepy to read the clock",
        "mistake": "drew extra eyes on a mask and claimed that six eyes never needed rest",
        "clue": "Mara pointed out that reliable helpers take turns and sleep between them",
        "plan": "made a shared schedule with rested adults and gave Kiri one early listening shift",
        "result": "Mara knew whom to call, and every helper remained rested enough to respond",
        "joke": "Pip asked the painted eyes why they were already snoring",
        "ending": "the schedule hung beside a quiet mask with six closed painted eyes",
    },
]


OPENINGS = [
    "The morning plan sounded simple until the forest added a complication.",
    "Kiri announced a grand invention before anyone had described the problem.",
    "At breakfast, one ordinary family chore turned into a puzzle.",
    "A small mishap began just as Pip claimed the day was unusually calm.",
    "Mara asked for a practical favor, and Kiri heard the word heroic.",
    "The tree-home was preparing for a baby, one sensible task at a time.",
    "Kiri had been studying the word evolution and was eager to demonstrate it.",
    "Pip noticed the trouble first, although Kiri supplied the loudest solution.",
    "Before the noon birds called, the family found a problem worth solving together.",
    "In a fictional forest far from Earth, a helpful plan began with a ridiculous mistake.",
]


def _story_index(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum(ord(ch) for ch in (params.hero_name + params.parent_name + params.companion_name))


def tell(params: StoryParams) -> World:
    index = _story_index(params)
    scenario_index = index % len(SCENARIOS)
    mode_index = (index // len(SCENARIOS)) % len(OPENINGS)
    scenario = {
        key: value.replace("Kiri", params.hero_name)
        .replace("Mara", params.parent_name)
        .replace("Pip", params.companion_name)
        for key, value in SCENARIOS[scenario_index].items()
    }
    w = World()
    hero = w.add(Entity(id=params.hero_name, kind="character", type="ewok", label="ewok"))
    parent = w.add(Entity(id=params.parent_name, kind="character", type="ewok", label="mother ewok"))
    sibling = w.add(Entity(id=params.companion_name, kind="character", type="ewok", label="small ewok"))
    basket = w.add(Entity(
        id="basket",
        type="basket",
        label="berry basket",
        phrase="a berry basket full of bright red fruit",
        caretaker=parent.id,
    ))
    sling = w.add(Entity(
        id="sling",
        type="gear",
        label="vine sling",
        phrase="a soft vine sling for carrying things",
    ))

    hero.memes["mischief"] += 1
    parent.meters["tiredness"] += 1
    _feel(parent, "care", 1)
    _feel(hero, "care", 1)

    w.say(OPENINGS[mode_index])
    w.say(
        f"In {params.place}, {hero.id}, {parent.id}, and {sibling.id} were Ewoks, "
        "the fictional furry forest creatures of this animal story."
    )
    w.say(
        f"{parent.id} was pregnant. She felt well enough to direct the day's work, "
        f"and she asked the others to {scenario['task']} because that would be more comfortable for her."
    )

    w.para()
    _feel(parent, "worry", 1)
    _bump(hero, "wobble", 1)
    _feel(hero, "mischief", 1)
    w.say(
        f"The difficulty was that {scenario['problem']}. {hero.id} wanted to solve it before asking any questions."
    )
    w.say(
        f"'Stand back for instant evolution!' {hero.id} cried, and {scenario['mistake']}."
    )
    w.say(f"{sibling.id} blinked. Then {scenario['joke']}. Even {parent.id} laughed.")
    _feel(hero, "humor", 1)
    _feel(parent, "humor", 1)

    w.para()
    w.say(
        f"'Learning a skill is not biological evolution,' {parent.id} explained. "
        "'In science, evolution happens across generations of living things. Today, you can simply revise your plan.'"
    )
    w.say(
        f"They paused to observe. The useful clue was that {scenario['clue']}. "
        f"'What would help you most?' {hero.id} asked. 'Listen first, then make the work easier,' {parent.id} replied."
    )
    w.say(f"Together they {scenario['plan']}.")
    _bump(hero, "readiness", 1)
    _feel(hero, "care", 1)
    _feel(sibling, "care", 1)

    w.para()
    w.say(f"The revised plan worked: {scenario['result']}.")
    parent.meters["tiredness"] = max(0.0, parent.meters["tiredness"] - 1)
    _bump(parent, "warmth", 1)
    _feel(parent, "relief", 1)
    _feel(parent, "love", 1)
    _feel(hero, "relief", 1)
    _feel(hero, "love", 1)
    w.say(
        f"{hero.id} had not biologically evolved in an afternoon. Instead, the young Ewok had changed a habit: "
        "ask, observe, and cooperate before building something enormous."
    )
    w.say(f"By evening, {scenario['ending']}.")

    w.facts.update(
        hero=hero,
        parent=parent,
        sibling=sibling,
        basket=basket,
        sling=sling,
        params=params,
        scenario=scenario,
        scenario_index=scenario_index,
        mode_index=mode_index,
        resolved=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    s = world.facts["scenario"]
    return [
        f"Write a humorous animal story about fictional Ewok {p.hero_name} learning to revise a plan while helping a pregnant family member.",
        f"Tell a gentle story in which the family must {s['task']}, using the clue that {s['clue']}.",
        "Write a child-facing story that distinguishes learning a better habit from biological evolution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    hero = f["hero"]
    parent = f["parent"]
    sibling = f["sibling"]
    s = f["scenario"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {p.hero_name}, a fictional Ewok who learned to help by listening and revising a plan."
        ),
        QAItem(
            question=f"What help did {parent.id} ask for?",
            answer=f"She asked the family to {s['task']}, because receiving that help was more comfortable for her during pregnancy."
        ),
        QAItem(
            question=f"What mistake did {p.hero_name} make first?",
            answer=f"{p.hero_name} {s['mistake']}. The funny failure showed that enthusiasm was not enough."
        ),
        QAItem(
            question="Which clue changed the family's plan?",
            answer=f"They noticed that {s['clue']}. That evidence led them to a more practical solution."
        ),
        QAItem(
            question=f"How did {p.hero_name} and {sibling.id} solve the problem?",
            answer=f"They {s['plan']}. As a result, {s['result']}."
        ),
        QAItem(
            question="Was the change in the story biological evolution?",
            answer=f"No. {hero.id} changed a learned habit during one afternoon, while biological evolution occurs across generations of living things."
        ),
    ]


KNOWLEDGE = [
    QAItem(
        question="What is an ewok in a story?",
        answer="An ewok is a small furry forest creature that can be brave, funny, and helpful."
    ),
    QAItem(
        question="What does pregnant mean?",
        answer="Pregnant means a person or animal has a developing baby growing in the uterus before birth."
    ),
    QAItem(
        question="What does evolution mean in simple science words?",
        answer="Evolution means living things change slowly over a very long time, and helpful traits can spread."
    ),
    QAItem(
        question="Why should helpers ask a pregnant person what support they want?",
        answer="Pregnancy affects individuals differently, so asking lets the person choose help that is useful and comfortable."
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_helped :- resolved.
funny_mistake :- mischief, not resolved.
pregnant_parent :- parent.
better_help :- resolved, hero_helped.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("ewok", "hero"),
        asp.fact("ewok", "parent"),
        asp.fact("ewok", "sibling"),
        asp.fact("pregnant", "parent"),
        asp.fact("basket", "berry_basket"),
        asp.fact("tool", "vine_sling"),
        asp.fact("theme", "humor"),
        asp.fact("theme", "animal_story"),
        asp.fact("theme", "evolution"),
        asp.fact("resolved"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    ok = any(sym.name == "resolved" for sym in model)
    if ok:
        print("OK: ASP reasoner sees the story as resolved.")
        return 0
    print("MISMATCH: ASP reasoner did not see resolution.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous ewok animal-story world.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--hero-name")
    ap.add_argument("--parent-name")
    ap.add_argument("--companion-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero_name or rng.choice(["Kiri", "Tomo", "Luma", "Nebi"])
    parent = args.parent_name or rng.choice(["Mara", "Suri", "Tala", "Nima"])
    companion = args.companion_name or rng.choice(["Pip", "Boko", "Rin", "Moki"])
    return StoryParams(
        seed=args.seed,
        hero_name=hero,
        parent_name=parent,
        companion_name=companion,
    )


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


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
    StoryParams(hero_name="Kiri", parent_name="Mara", companion_name="Pip"),
    StoryParams(hero_name="Tomo", parent_name="Suri", companion_name="Boko"),
    StoryParams(hero_name="Luma", parent_name="Tala", companion_name="Rin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/0."))
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
