#!/usr/bin/env python3
"""A varied, state-grounded superhero StoryWorld about teamwork and self-control."""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
sys.path.insert(0, str(STORYWORLDS_DIR.parent))
from results import QAItem, StorySample  # noqa: E402

TITLE = "Chief, Urge, Bows"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        forms = {
            "Chief Leo": {"subject": "he", "object": "him", "possessive": "his"},
            "Chief Mina": {"subject": "she", "object": "her", "possessive": "her"},
            "Chief Koa": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return forms.get(self.label, forms["Chief Koa"])[case]


@dataclass
class StoryParams:
    chief_name: str = "Chief Leo"
    urge: str = "rush to the parade"
    bows: str = "silk bows"
    place: str = "the city square"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    name: str
    mission: str
    problem: str
    clue: str
    first_attempt: str
    consequence: str
    team_plan: str
    rhyme: str
    resolution: str
    ending: str
    helpers: tuple[str, str, str]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


INCIDENTS = [
    Incident(
        "windy welcome", "decorate the welcome arch before the parade arrived",
        "a gust kept lifting the ribbon bows from their numbered pegs",
        "one loose ribbon pointed straight toward a rattling roof vent",
        "grabbed at every fluttering bow at once", "two bows slipped farther across the mat",
        "the scout closed the vent, the painter sorted colors, and the drummer clipped each soft ribbon to its peg",
        "Clip by clip, let breezes skip; sort each hue, then check it through!",
        "the airflow calmed and every ribbon bow returned to its matching peg",
        "the welcome arch rippled gently while twelve tidy bows shone in the afternoon light",
        ("the scout", "the painter", "the drummer"),
    ),
    Incident(
        "mixed-up messages", "prepare thank-you bows for the neighborhood helpers",
        "the labels had fallen from three gift baskets, so nobody knew which bow belonged where",
        "tiny flecks of blue paper clung to one basket handle", "guessed by choosing the brightest bow",
        "the guessed bow covered the card meant to identify the basket",
        "the librarian matched paper flecks, the baker read the cards aloud, and the mechanic made a clear sorting tray",
        "Read the clue, match the blue; share the task and check it through!",
        "the team matched every soft gift bow without hiding a single card",
        "each helper found a named basket waiting beneath a neat ribbon curl",
        ("the librarian", "the baker", "the mechanic"),
    ),
    Incident(
        "sticky stage", "finish a bow-shaped backdrop for the team show",
        "a jar of washable paste tipped over and made the ribbon loops cling together",
        "the paste label said that warm water would loosen it", "pulled one loop with a sharp tug",
        "the damp paper backdrop began to crease",
        "the nurse fetched towels, the inventor measured warm water, and the acrobat held the backdrop flat",
        "Dab, don't drag; smooth each snag. Pat it slow and watch it glow!",
        "gentle dabs released the loops and kept the paper from tearing",
        "the dry backdrop opened like a sunrise behind the team's final pose",
        ("the nurse", "the inventor", "the acrobat"),
    ),
    Incident(
        "runaway wagon", "deliver boxes of ribbon bows to the children's fair",
        "the little supply wagon rolled whenever the sloped pavement shook",
        "a chalk line showed that one wheel stop was missing", "tried to hold the wagon and stack a box at the same time",
        "the top box tilted, though no one stood in its path",
        "the crossing guard cleared the slope, the builder set a wheel block, and the runner carried one light box at a time",
        "Block the wheel, test and feel; lift in pairs and show we care!",
        "the secured wagon stayed still while the team delivered every box safely",
        "soft bows filled the fair booth as the empty wagon rested behind its bright wheel block",
        ("the crossing guard", "the builder", "the runner"),
    ),
    Incident(
        "missing pattern", "rebuild the giant ribbon-bow mosaic on the plaza floor",
        "the picture guide was smudged and the final row looked backward",
        "a clean reflection of the pattern remained in a nearby shop window", "started copying the smudged row from memory",
        "the star at the center became a crooked zigzag",
        "the photographer studied the reflection, the dancer marked the center, and the gardener laid out colors in order",
        "Find the star, near and far; line by line, the clues align!",
        "the reflected clue helped the team restore the bow mosaic from its center outward",
        "the completed star gleamed between loops of red, gold, and blue ribbon",
        ("the photographer", "the dancer", "the gardener"),
    ),
    Incident(
        "quiet signal", "hang ribbon bows that would guide families to the calm corner",
        "the noisy rehearsal drowned out the directions for where each color should go",
        "the map used matching shapes as well as colors", "called the instructions louder than the drums",
        "everyone heard noise but still missed the order",
        "the mapper held up shape cards, the drummer paused between beats, and the mime pointed to each matching hook",
        "Circle, square, place with care; pause, then show which bow should go!",
        "silent shape signals guided every ribbon bow to the correct hook",
        "families followed the calm row of bows to a nook where paper lanterns glowed",
        ("the mapper", "the drummer", "the mime"),
    ),
    Incident(
        "rainy rehearsal", "protect the parade bows before a sudden shower",
        "raindrops spotted the ribbons while the cover lay folded in the supply chest",
        "the darkest drops fell beneath a gap in the awning", "rushed to move the whole rack alone",
        "one wheel bumped the curb and made the rack wobble",
        "the weather watcher found the leak, the carpenter steadied the rack, and the tailor spread the cover from the dry side",
        "Spot the drip, steady grip; cover wide, then roll inside!",
        "the team covered the bows and rolled the steady rack beneath the sound awning",
        "dry ribbons framed a puddle that reflected the clearing sky after the shower",
        ("the weather watcher", "the carpenter", "the tailor"),
    ),
    Incident(
        "shadow mix-up", "place bows along the evening lantern path",
        "long shadows made two hooks look occupied when they were actually bare",
        "a lantern moved, but the supposed bows did not move with it", "counted the shadows as if they were real ribbon bows",
        "the total came out right even though two hooks remained empty",
        "the astronomer shifted the lantern, the teacher counted real knots, and the skater carried two spare bows",
        "Count the knot, not the spot; move the light and make it right!",
        "the changing light revealed the empty hooks and the team filled them",
        "real bows fluttered between lantern pools while their shadows danced in the dusk",
        ("the astronomer", "the teacher", "the skater"),
    ),
    Incident(
        "bell tower delivery", "raise a basket of ribbon bows to the bell-tower balcony",
        "the hand-cranked lift stopped halfway because its guide rope had crossed",
        "a painted arrow showed the rope belonged on the other side of the guide", "pulled harder on the crank",
        "the basket stayed still and the rope tightened",
        "the engineer locked the crank, the climber checked from the safe stairs, and the singer relayed each instruction",
        "Lock, look, speak; never yank or sneak. Cross it right, then lift it light!",
        "an adult uncrossed the guide rope, and the team raised the light basket slowly",
        "the balcony rail bloomed with ribbon bows just as the first bell chimed",
        ("the engineer", "the climber", "the singer"),
    ),
    Incident(
        "color promise", "divide ribbon bows fairly among four neighborhood floats",
        "one float seemed to have fewer bows because its dark ribbons blended into the cloth",
        "the packing list gave every float the same number", "offered it bows from another float before counting",
        "the generous move would have left a different team short",
        "the bookkeeper read the list, the artist spread each set on a pale mat, and the cyclist delivered the counted bundles",
        "Spread and see, count by three; fair for you and fair for me!",
        "the pale mats revealed the hidden dark bows and confirmed four equal sets",
        "all four floats rolled out wearing equal fans of ribbon beneath their name signs",
        ("the bookkeeper", "the artist", "the cyclist"),
    ),
    Incident(
        "garden visitors", "decorate a garden gate without disturbing visiting butterflies",
        "the first ribbon position brushed the flowers where butterflies were feeding",
        "the insects kept circling an empty upper rail instead", "waved the bows to hurry the butterflies away",
        "the frightened visitors scattered and the flowers shook",
        "the naturalist waited quietly, the gardener chose the upper rail, and the seamstress tied loose bows well above the blooms",
        "Wait and know, watch them go; tie up high where wings pass by!",
        "the team moved the decorations away from the flowers and gave the butterflies room",
        "butterflies settled on the blooms beneath a high row of softly swaying bows",
        ("the naturalist", "the gardener", "the seamstress"),
    ),
    Incident(
        "finale countdown", "release a curtain of ribbon bows for the superhero finale",
        "the numbered pull cords had been threaded through the wrong cardboard rings",
        "cord three moved the bow marked one during a careful floor-level test", "reached for all three cords before the countdown",
        "the test curtain bunched instead of opening",
        "the stage manager stopped the countdown, the coder traced each number, and the puppeteer rethreaded the loose cords with the power off",
        "Test one line, match each sign; stop, reset, then cue the set!",
        "the corrected numbers let the team release each light ribbon bow in order",
        "three bright bows unfolded above the cheering team like friendly flags on the final beat",
        ("the stage manager", "the coder", "the puppeteer"),
    ),
]

ROUTES = [
    ("A tiny warning became the first clue.", "The team treated the clue like a superhero signal."),
    ("The mission began smoothly, until one detail refused to fit.", "Instead of guessing again, the team compared what each helper had noticed."),
    ("For one hopeful minute, everything looked ready.", "Then the chief asked everyone to pause and test the evidence."),
    ("The team had practiced the mission twice.", "Their practice paid off: each helper knew when to stop and listen."),
    ("A child in the crowd noticed the trouble first.", "The chief thanked the careful observer and invited the team to investigate."),
    ("The trouble arrived quietly rather than with a crash.", "Three different observations joined into one useful answer."),
    ("The chief's checklist said, 'Look, ask, then act.'", "This time the team followed every word of that checklist."),
    ("A superhero badge could not solve this mission by itself.", "Listening turned out to be the team's strongest power."),
    ("Everyone wanted the celebration to begin on time.", "They chose a careful delay over a hurried mistake."),
    ("The bows looked simple, but the mission required patient eyes.", "Once every voice had a turn, the hidden cause became clear."),
]

SETTINGS = ["the city square", "the rooftop", "the parade route"]
URGES = ["rush to the parade", "jump into the spotlight", "dash off before the plan was ready"]
BOWS = ["silk bows", "red ribbon bows", "gold parade bows"]
CHIEFS = ["Chief Leo", "Chief Mina", "Chief Koa"]


def _display_name(chief: Entity) -> str:
    return chief.label.removeprefix("Chief ")


def choose_incident(params: StoryParams) -> tuple[Incident, int]:
    seed = params.seed if params.seed is not None else 0
    return INCIDENTS[seed % len(INCIDENTS)], (seed // len(INCIDENTS)) % len(ROUTES)


def setup_world(params: StoryParams, incident: Incident, route_index: int) -> World:
    world = World(params.place)
    chief = world.add(Entity(id="chief", kind="character", type="chief", label=params.chief_name, phrase=params.chief_name))
    bows = world.add(Entity(
        id="bows", kind="thing", type="bows", label=params.bows, phrase=f"a bundle of {params.bows}",
        owner=chief.id, caretaker="team", plural=True,
    ))
    world.facts.update(
        chief=chief, bows=bows, place=params.place, urge=params.urge, incident=incident,
        route_index=route_index, role="rotating team chief",
        bow_safety="soft ribbon decorations, not archery equipment",
    )
    return world


def tell(params: StoryParams) -> World:
    incident, route_index = choose_incident(params)
    route_open, route_turn = ROUTES[route_index]
    world = setup_world(params, incident, route_index)
    chief = world.get("chief")
    bows = world.get("bows")
    pronoun = chief.pronoun()
    possessive = chief.pronoun("possessive")

    world.say(
        f"At {world.place}, {_display_name(chief)} wore the Chief badge for the day. Chief was a rotating team job: "
        "the person wearing the badge listened, organized the helpers, and kept everyone safe."
    )
    world.say(
        f"The superhero team's mission was to {incident.mission} using {bows.phrase}. "
        "These bows were soft ribbon decorations, never archery equipment."
    )
    world.say(route_open)
    world.para()

    world.say(f"Soon, {incident.problem}. {incident.clue.capitalize()}.")
    world.say(
        f"A strong urge tugged at {possessive} thoughts: {params.urge}. "
        f'"I want to hurry," {chief.label} admitted, "but a chief should hear the team first."'
    )
    world.say(f"For a moment, {pronoun} {incident.first_attempt}. As a result, {incident.consequence}.")
    chief.memes["urge"] = 1
    bows.meters["problem"] = 1
    world.fired.add(("urge_caused_setback", incident.name))
    world.para()

    world.say(route_turn)
    world.say(f'{chief.label} raised one open hand. "Teamwork time. Tell me what you saw, and we will choose the safest plan."')
    helpers = list(incident.helpers)
    world.say(f"Together, {incident.team_plan}.")
    world.say(f'They kept their steps together with a rhyme: "{incident.rhyme}"')
    world.facts.update(
        helpers=helpers, clue=incident.clue, setback=incident.consequence,
        team_plan=incident.team_plan, resolution=incident.resolution,
    )
    world.fired.add(("team_investigated", incident.name))
    world.para()

    bows.meters["problem"] = 0
    bows.meters["safe_and_ready"] = 1
    chief.memes["patience"] = 1
    chief.memes["teamwork"] = 1
    world.say(f"Because they followed the clue and shared the work, {incident.resolution}.")
    world.say(
        f'{chief.label} let the urge pass and stayed until the mission was safe. '
        f'"Being chief does not mean doing everything," {pronoun} said. "It means helping everyone do their part."'
    )
    world.say(f"By the happy ending, {incident.ending}.")
    world.fired.add(("mission_completed", incident.name))
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    incident = facts["incident"]
    return [
        f'Write a child-friendly superhero story about {facts["chief"].label}, whose urge to {facts["urge"]} complicates a mission at {facts["place"]}.',
        f'Tell how teamwork, a clue in the {incident.name} mission, and a rhyme help make {facts["bows"].label} safe and ready.',
        'Write a complete story using "chief," "urge," and "bows," where chief is a team job and bows are ribbon decorations.',
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    chief = facts["chief"]
    bows = facts["bows"]
    incident = facts["incident"]
    helpers = ", ".join(facts["helpers"][:-1]) + ", and " + facts["helpers"][-1]
    return [
        QAItem(
            question=f"What did the title Chief mean for {chief.label}?",
            answer="Chief was a rotating team job. The person wearing the badge listened, organized helpers, and kept everyone safe.",
        ),
        QAItem(
            question=f"What urge made the {incident.name} mission harder?",
            answer=f"{chief.label} felt an urge to {facts['urge']}. Acting on it too quickly caused this setback: {facts['setback']}.",
        ),
        QAItem(
            question="What clue helped the team understand the problem?",
            answer=f"The team noticed that {facts['clue']}. They used that evidence instead of making another guess.",
        ),
        QAItem(
            question=f"How did the helpers use teamwork with the {bows.label}?",
            answer=f"{helpers} shared the work: {facts['team_plan']}. Their rhyme helped them move carefully together.",
        ),
        QAItem(
            question="What changed by the end of the mission?",
            answer=f"{facts['resolution'].capitalize()}. The bows were safe and ready, and {chief.label} learned to listen before acting.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is teamwork?", answer="Teamwork means people share information and different jobs to reach a goal together."),
        QAItem(question="What is a rhyme?", answer="A rhyme uses words with matching end sounds. A short rhyme can help a team remember ordered steps."),
        QAItem(question="What kind of bows appear in this StoryWorld?", answer="The bows are soft ribbon decorations. They are not bows used for archery."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== (3) World knowledge questions =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("chief", "chief"), "teamwork.", "rhyme."]
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for urge in URGES:
        lines.append(asp.fact("urge", urge))
    for bows in BOWS:
        lines.append(asp.fact("bows", bows))
    return "\n".join(lines)


ASP_RULES = r"""
risky(U) :- urge(U).
needs_plan(B) :- bows(B), risky(_).
fixes(B) :- bows(B), teamwork, rhyme.
good_story :- fixes(_).
#show risky/1.
#show needs_plan/1.
#show fixes/1.
#show good_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/0."))
    if model is not None and asp.atoms(model, "good_story"):
        print("OK: ASP program grounded and found a teamwork resolution.")
        return 0
    print("ASP verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero story world: chief, urge, bows, teamwork, rhyme.")
    parser.add_argument("--chief-name", choices=CHIEFS, default=None)
    parser.add_argument("--urge", choices=URGES, default=None)
    parser.add_argument("--bows", choices=BOWS, default=None)
    parser.add_argument("--place", choices=SETTINGS, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        chief_name=args.chief_name or rng.choice(CHIEFS), urge=args.urge or rng.choice(URGES),
        bows=args.bows or rng.choice(BOWS), place=args.place or rng.choice(SETTINGS), seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params, story=world.render(), prompts=generation_prompts(world),
        story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world,
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
    StoryParams(chief_name="Chief Leo", urge="rush to the parade", bows="silk bows", place="the city square", seed=0),
    StoryParams(chief_name="Chief Mina", urge="jump into the spotlight", bows="red ribbon bows", place="the rooftop", seed=37),
    StoryParams(chief_name="Chief Koa", urge="dash off before the plan was ready", bows="gold parade bows", place="the parade route", seed=74),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show risky/1. #show needs_plan/1. #show fixes/1. #show good_story/0."))
        for predicate in ("risky", "needs_plan", "fixes", "good_story"):
            print(asp.atoms(model, predicate))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.chief_name} / {params.urge} / {params.bows}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
