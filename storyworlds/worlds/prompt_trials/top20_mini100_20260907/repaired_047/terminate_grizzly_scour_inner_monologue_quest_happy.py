#!/usr/bin/env python3
"""
A standalone superhero storyworld about a hero's quest with inner monologue and a happy ending.

Seed words: terminate, grizzly, scour
Style: Superhero Story
Features: Inner Monologue, Quest, Happy Ending
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[3]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402

ASP_RULES = r"""
% A superhero quest is reasonable when the mission is risky but solvable.
hero_story(S) :- quest(S), has_inner_monologue(S), has_happy_ending(S).
good_mission(M) :- mission(M), can_terminate_threat(M), can_scour_clues(M).
happy_finish(S) :- hero_story(S), good_mission(_).
"""

SETTING = "city skyline"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    hero: str
    partner: str
    threat: str
    tool: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    trouble: str
    inner_thought: str
    dialogue: str
    clue: str
    action: str
    turn: str
    ending: str
    lesson: str


@dataclass
class World:
    place: str = SETTING
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={dict(e.meters)}")
            if e.memes:
                bits.append(f"memes={dict(e.memes)}")
            if e.label:
                bits.append(f"label={e.label!r}")
            lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


@dataclass(frozen=True)
class Registry:
    heroes: tuple[str, ...]
    partners: tuple[str, ...]
    threats: tuple[str, ...]
    tools: tuple[str, ...]


REGISTRY = Registry(
    heroes=("Nova", "Blink", "Aurora", "Vector", "Pulse", "Comet", "Mira", "Atlas"),
    partners=("kid sidekick", "rookie reporter", "brave friend", "tech helper", "tiny scout", "city helper"),
    threats=("grizzly shadow", "rooftop grizzly drone", "bear-mask brute", "grizzly machine", "scouring smoke beast"),
    tools=("signal ring", "sky grappler", "bright shield", "zoom lens", "pulse baton", "glider cape"),
)


def reasonableness_gate(params: StoryParams) -> None:
    if not params.hero.strip():
        raise StoryError("A superhero story needs a hero name.")
    if not params.partner.strip():
        raise StoryError("A superhero story needs a partner or helper.")
    if not params.threat.strip():
        raise StoryError("A quest needs a clear threat to face.")
    if not params.tool.strip():
        raise StoryError("A hero needs one useful tool for the quest.")


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("quest", "city_quest"),
        asp.fact("has_inner_monologue", "city_quest"),
        asp.fact("has_happy_ending", "city_quest"),
        asp.fact("mission", "city_quest"),
        asp.fact("can_terminate_threat", "city_quest"),
        asp.fact("can_scour_clues", "city_quest"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


SCENARIOS = [
    Scenario(
        key="rooftop_tracks",
        premise="was watching the moonlight blink across the rooftops when the alarm sounded",
        trouble="A grizzly shadow kept circling the clock tower and scattering pigeons from every ledge.",
        inner_thought="If the shadow keeps moving, I need to scour the rooftops for the pattern before I can terminate the danger.",
        dialogue='"Can you keep watch below?" the hero asked. "I can, if you tell me what you find," the partner replied.',
        clue="three scraped chimneys made a trail that pointed to the old billboard",
        action="used the sky grappler to swing closer, then read the trail of marks like a map",
        turn="The marks were not from a monster at all; they were from a broken smoke machine hiding a frightened kitten in the billboard frame.",
        ending="The hero shut the machine down, freed the kitten, and the grizzly shadow vanished into a harmless pile of soot.",
        lesson="a brave hero can solve a big mystery by looking carefully before striking",
    ),
    Scenario(
        key="subway_echo",
        premise="had promised to keep the city safe before the late train rolled in",
        trouble="A grizzly drone clanged through the empty subway tunnel, and its siren made every car tremble.",
        inner_thought="Stay calm. First scour for the control signal, then terminate the drone without hurting anyone riding home.",
        dialogue='"That sound is coming from deeper in the tunnel," the partner said. "Then that is where we go," the hero answered.',
        clue="a blinking red light bounced off the rails whenever the drone turned left",
        action="swung the bright shield to mirror the signal and followed the flashes to a hidden panel",
        turn="Behind the panel, the hero found a jammed switch that had trapped the drone in a loop of alarms.",
        ending="One careful press stopped the machine, and the quiet train tunnel felt safe again.",
        lesson="the smartest quest ends danger by fixing the cause, not by making more noise",
    ),
    Scenario(
        key="museum_mist",
        premise="was guarding the city museum during a stormy evening",
        trouble="A grizzly fog crept through the gallery and wrapped the statues in a cold gray blanket.",
        inner_thought="Fog can hide trouble, so I need to scour every room for the source before I terminate the breach.",
        dialogue='"I found wet footprints!" the partner whispered. "Great," the hero said, "then the fog must have a door."',
        clue="the footprints stopped at a cracked skylight above the dinosaur hall",
        action="lifted the glider cape, climbed to the skylight, and sealed the gap with a metal patch",
        turn="The fog was only steam from a burst pipe in the roof, and once it cooled, the gallery cleared at once.",
        ending="The statues stood bright and dry by morning, and the museum lights glowed like friendly stars.",
        lesson="careful searching can turn a scary mystery into a simple repair",
    ),
    Scenario(
        key="harbor_rumble",
        premise="was racing along the harbor wall while gulls circled overhead",
        trouble="A grizzly brute was shoving crates into the water and laughing as the waves swallowed them.",
        inner_thought="He looks strong, but I can still scour the dock for leverage and terminate the chaos without a brawl.",
        dialogue='"Take the rope ladder!" the partner shouted. "Already on it!" the hero called back.',
        clue="one crate had a fresh scratch that matched the teeth on a broken crane hook",
        action="hooked the crane line, pulled the broken lever free, and used it to lock the brute's cart in place",
        turn="The brute had been trying to stop a loose cart from rolling into the harbor, but panic had turned his fix into a mess.",
        ending="Together they steadied the cart, saved the crates, and the hero helped the brute carry the last box home.",
        lesson="a hero can win a quest by helping even the person who caused the trouble",
    ),
    Scenario(
        key="park_signal",
        premise="was patrolling the park benches just after sunset",
        trouble="A grizzly shape kept flashing across the pond and making the ducks scatter in circles.",
        inner_thought="That shape is too smooth to be real. Scour the water, find the trick, and terminate the scare.",
        dialogue='"The reflection is moving wrong," the partner said. "Then someone is using it as a mask," the hero replied.',
        clue="ripples on the pond lined up with a small drone hidden in the reeds",
        action="used the zoom lens to spot the drone, then waved the signal ring to shut it off",
        turn="When the drone stopped, the grizzly shape on the water disappeared and revealed a tired puppet on a string.",
        ending="The ducks paddled back, the pond went still, and the park looked cheerful again under the lamps.",
        lesson="sometimes the scariest thing is only a trick that can be switched off",
    ),
    Scenario(
        key="library_alarm",
        premise="was finishing a quiet patrol at the city library",
        trouble="A grizzly rattle came from the reference room, where the bookshelves stretched higher than the stairs.",
        inner_thought="A shelf this tall could hide anything. I need to scour the stacks before I terminate the threat.",
        dialogue='"I heard pages rustling by the atlas shelf," the partner said. "Then we start there," the hero said.',
        clue="a trail of torn paper led to a stuck rolling ladder",
        action="climbed the ladder, freed the jam, and used the bright shield to check behind the shelves",
        turn="Behind the books, the hero found a little robot sorting pages too quickly and knocking volumes loose by accident.",
        ending="The robot slowed down, the books stayed safe, and the library returned to its warm, peaceful hush.",
        lesson="not every alarm is a villain; some problems only need patience and care",
    ),
    Scenario(
        key="bridge_shake",
        premise="was crossing the river bridge when the wind snapped at the cables",
        trouble="A grizzly tremor ran through the bridge each time a heavy truck passed, and the lamps flickered.",
        inner_thought="If the bridge fails, the whole avenue closes. I must scour the cables and terminate the weak point fast.",
        dialogue='"Do you hear that hum?" the partner asked. "Yes," the hero said, "and it means one cable is loose."',
        clue="one cable sang louder than the others whenever the wind turned east",
        action="secured the loose cable with the tool belt clasp and guided the next truck to cross slowly",
        turn="The weak cable was only rubbing against a bent sign, and the shaking stopped once the sign was pushed flat.",
        ending="The bridge held steady, the lights brightened, and the city traffic rolled home in peace.",
        lesson="a careful fix can save everyone from a problem that sounded much bigger than it was",
    ),
]

OPENINGS = [
    "Night had just settled over the {setting} when {hero} listened for trouble from the sky.",
    "Before dawn, {hero} stepped onto the {setting} roof and felt a quest begin in the wind.",
    "The city lights below the {setting} glimmered like stars as {hero} prepared for patrol.",
    "Inside the {setting}, an old alarm chirped once, and {hero} knew the night was not finished.",
    "A gust swept past the {setting}, carrying news of a problem only a hero could solve.",
]

REACTIONS = [
    '"This looks big," {hero} muttered, "but big is only a clue that I should look harder."',
    '"Stay calm," {hero} told themself. "A real hero can terminate fear after finding the truth."',
    '"I can do this," {hero} thought. "First scour, then strike, then help."',
    '"The city needs a careful hero, not a hurried one," {hero} reminded themself.',
]

PLANS = [
    "Together they agreed to search one block at a time and follow every small sign.",
    "They split the quest into two parts: the partner watched the street while the hero climbed high.",
    "They chose the safest route first so no one in the city would be put at risk.",
    "They kept their voices low and searched for the real source of the trouble.",
]

CELEBRATIONS = [
    "The partner grinned. \"We make a strong team,\" they said, and the hero nodded with relief.",
    "\"Quest complete,\" the hero said softly, and the partner answered, \"And the city is safer now.\"",
    "They bumped fists under the streetlamp, both proud that the ending felt kind.",
    "The hero thanked the partner for the clue, and the partner laughed at how quickly the danger had changed.",
]

TOOLS = {
    "signal ring": "sent a clear pulse through the air",
    "sky grappler": "caught the nearest ledge and pulled the hero upward",
    "bright shield": "flashed light into the dark corner",
    "zoom lens": "brought the smallest clue into focus",
    "pulse baton": "gave the hidden machine a harmless shutoff tap",
    "glider cape": "lifted the hero toward the high place where the clue waited",
}


NAMES = REGISTRY.heroes
PARTNERS = REGISTRY.partners
THREATS = REGISTRY.threats
TOOLS_LIST = REGISTRY.tools


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        hero=rng.choice(NAMES),
        partner=rng.choice(PARTNERS),
        threat=rng.choice(THREATS),
        tool=rng.choice(TOOLS_LIST),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero quest storyworld with inner monologue and happy ending.")
    ap.add_argument("--hero")
    ap.add_argument("--partner")
    ap.add_argument("--threat")
    ap.add_argument("--tool", choices=TOOLS_LIST)
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
    params = valid_params(rng)
    if args.hero:
        params.hero = args.hero
    if args.partner:
        params.partner = args.partner
    if args.threat:
        params.threat = args.threat
    if args.tool:
        params.tool = args.tool
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", label=params.hero))
    partner = world.add(Entity(id="partner", kind="character", label=params.partner))
    threat = world.add(Entity(id="threat", kind="thing", label=params.threat))
    tool = world.add(Entity(id="tool", kind="thing", label=params.tool))
    world.facts.update(
        hero=hero,
        partner=partner,
        threat=threat,
        tool=tool,
        place=SETTING,
        quest=True,
        inner_monologue=True,
        happy_ending=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    partner = world.get("partner")
    threat = world.get("threat")
    tool = world.get("tool")

    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    opening = rng.choice(OPENINGS).format(setting=SETTING, hero=hero.label)
    reaction = rng.choice(REACTIONS).format(hero=hero.label)
    plan = rng.choice(PLANS)
    celebration = rng.choice(CELEBRATIONS)
    tool_action = TOOLS[tool.label]

    hero.bump_meme("focus")
    partner.bump_meme("trust")
    threat.bump_meter("danger", 1.0)

    world.say(opening)
    world.say(
        f"{hero.label} and {partner.label} spotted {threat.label}, and the hero's quest began in earnest. "
        f"At the start of the mission, {hero.label} {scenario.premise}."
    )
    world.para()

    world.say(scenario.trouble)
    world.say(reaction)
    world.say(f"{hero.label}'s inner monologue said, '{scenario.inner_thought}'")
    world.para()

    world.say(scenario.dialogue)
    world.say(plan)
    world.say(f"Then {hero.label} {scenario.clue} and decided that the next move had to terminate the scare, not the city.")
    world.para()

    tool.bump_meter("used", 1.0)
    hero.bump_meter("airtime", 1.0)
    world.say(f"With the {tool.label}, {hero.label} {tool_action}.")
    world.say(f"That careful move let the hero {scenario.action}.")
    world.say(scenario.turn)
    world.para()

    threat.bump_meter("danger", -1.0)
    hero.bump_meme("joy", 1.0)
    partner.bump_meme("joy", 1.0)
    world.say(celebration)
    world.say(f"{hero.label} thought, 'I did not just fight the problem; I learned it.'")
    world.say(f"By the end, {scenario.ending} {scenario.lesson} The {threat.label} was gone, and the quest ended happily.")
    world.facts.update(
        scenario=scenario.key,
        premise=scenario.premise,
        trouble=scenario.trouble,
        inner_thought=scenario.inner_thought,
        clue=scenario.clue,
        action=scenario.action,
        turn=scenario.turn,
        ending_image=scenario.ending,
        lesson=scenario.lesson,
        resolved=True,
        terminate=True,
        scour=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story in the {SETTING} where {f['hero'].label} goes on a quest to help {f['partner'].label}.",
        f"Tell a child-friendly story that uses the words terminate, grizzly, and scour, and ends happily.",
        f"Write a story with inner monologue and dialogue where a hero faces {f['threat'].label} and uses {f['tool'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What trouble started the hero's quest?",
            answer=str(f["trouble"]),
        ),
        QAItem(
            question="What did the hero think during the mission?",
            answer=str(f["inner_thought"]),
        ),
        QAItem(
            question="What clue helped the hero understand the problem?",
            answer=f"The clue was that {f['clue']}.",
        ),
        QAItem(
            question="How did the hero use the tool?",
            answer=f"The hero used the {f['tool'].label} to {f['action']}.",
        ),
        QAItem(
            question="What proved the story had a happy ending?",
            answer=f"The danger was resolved when {f['ending_image']} The quest ended happily.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is when a character thinks to themself inside the story.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to solve an important problem.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the danger is solved and the story ends in a good way.",
        ),
    ]


def dump_trace(world: World) -> str:
    return world.trace()


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


def asp_verify() -> int:
    import asp

    program = asp_program("#show hero_story/1.\n#show happy_finish/1.\n#show good_mission/1.")
    model = asp.one_model(program)
    atoms = set((sym.name, tuple(arg.name if arg.type != 1 else arg.string for arg in sym.arguments)) for sym in model)
    expected = {
        ("hero_story", ("city_quest",)),
        ("happy_finish", ("city_quest",)),
        ("good_mission", ("city_quest",)),
    }
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show hero_story/1."))
    return sorted(set(asp.atoms(model, "hero_story")))


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
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
    StoryParams(hero="Nova", partner="kid sidekick", threat="grizzly shadow", tool="signal ring", seed=11),
    StoryParams(hero="Blink", partner="rookie reporter", threat="grizzly drone", tool="bright shield", seed=29),
    StoryParams(hero="Aurora", partner="tech helper", threat="grizzly fog", tool="zoom lens", seed=47),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show hero_story/1.\n#show happy_finish/1.\n#show good_mission/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP-compatible superhero quest stories:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
