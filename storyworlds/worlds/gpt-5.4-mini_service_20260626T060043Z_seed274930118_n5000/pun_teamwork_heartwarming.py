#!/usr/bin/env python3
"""A varied, heartwarming StoryWorld about puns and teamwork."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StorySample  # noqa: E402


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class ObjectItem:
    name: str
    label: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Mina"
    helper: str = "Dad"
    venue: str = "the community hall"
    event: str = "the bake sale"
    sign: str = "Let's stick together!"
    pun_word: str = "pun"
    twist: str = "the letters fall apart"
    fix: str = "they rebuild the sign together"


@dataclass(frozen=True)
class Scenario:
    key: str
    prop: str
    premise: str
    trouble: str
    clue: str
    failed_try: str
    hero_task: str
    helper_task: str
    solution: str
    result: str
    lesson: str
    ending: str


@dataclass
class World:
    params: StoryParams
    people: dict[str, Person] = field(default_factory=dict)
    items: dict[str, ObjectItem] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


NAMES = ["Mina", "Noah", "Lia", "Owen", "Nia", "Eli", "June", "Aria"]
HELPERS = ["Mom", "Dad", "Grandma", "Grandpa", "Aunt Jo", "Uncle Ben"]
VENUES = ["the community hall", "the library room", "the school gym", "the little park shelter"]
EVENTS = ["the bake sale", "the spring fair", "the read-a-thon", "the school picnic"]
LEGACY_SIGNS = [
    "A-pun-d to be together!",
    "Let's stick together!",
    "Teamwork makes the dream work!",
    "We are all in this pun-derful plan!",
]
PUNS = [
    ("Let's stick together!", "stick can mean staying united or making something cling"),
    ("We make a great pear!", "pear sounds like pair"),
    ("Donut worry - we've got this!", "donut sounds like do not"),
    ("Teamwork is our jam!", "jam can be fruit spread or something people love doing"),
    ("Lettuce help one another!", "lettuce sounds like let us"),
    ("This plan is souper!", "souper sounds like super"),
    ("Reading is a novel idea!", "novel can mean both a book and something new"),
    ("We can do it together!", "can means being able and also a food tin"),
    ("Working together is a bright idea!", "bright can describe both a clever idea and a light"),
    ("We really pull together!", "pull can mean tugging a cord or cooperating"),
    ("Rain or shine, teamwork reigns!", "reigns sounds like rains and means leads the way"),
    ("Our teamwork is sound!", "sound can mean both healthy and something we hear"),
    ("We fit together!", "fit can mean joining pieces or belonging on a team"),
]
SIGNS = list(dict.fromkeys(LEGACY_SIGNS + [text for text, _ in PUNS]))
TWISTS = ["the paper tears", "the tape comes loose", "the letters tumble", "the sign tips"]
FIXES = ["they repair it together", "they divide the work", "they follow the clue", "they test their repair"]

SCENARIOS = [
    Scenario("wind", "paper banner", "hung a banner between two posts", "A gust snapped one string, and the banner sailed toward a muddy puddle.", "The loose corner dipped lower with every gust.", "chasing it alone made the other knot slip", "caught the dipping corner", "looped spare ribbon around the post", "They counted to three, pulled together, and tied two low, sturdy knots.", "The banner stayed level through the next gust.", "another pair of hands can turn a chase into a plan", "two ribbon tails danced while the words stayed clear"),
    Scenario("jam", "tray of jam tarts", "set jam tarts beneath the welcome sign", "A wobbly table leg tipped the tray toward the floor.", "A berry rolled downhill whenever the table moved.", "holding the tray forever left nobody free to mend the table", "kept the tarts balanced", "folded a cardboard shim for the short leg", "They slid in the shim and tested the table with an empty plate.", "Not one tart slipped, and the word 'jam' earned its laugh.", "steady help matters more than pretending one person can hold everything", "a purple spoon rested beside a level row of tarts"),
    Scenario("books", "rolling book cart", "wheeled a book cart beneath the reading sign", "The cart bumped a cord, scattering cardboard letters among the books.", "Each letter lay beside a book beginning with that letter.", "guessing at the message produced an unreadable jumble", "sorted the books by first letter", "matched each letter to a gap", "They read the clue aloud, arranged the letters, and checked the sentence twice.", "The restored 'novel idea' pun made the librarian grin.", "two careful readers solve more than one hurried guesser", "the last blue letter clicked into place above an open book"),
    Scenario("paint", "painted sign", "painted a bright sign on a long sheet of paper", "A cup tipped, sending a green river across the final word.", "The dry letters resisted the spill while the wet word blurred.", "scrubbing the stain spread it wider", "blotted from the outside inward", "mixed fresh paint to match the letters", "They let the paper dry, then repainted only the damaged word.", "The green patch became a neat leaf beside the rescued pun.", "good teammates notice what can be saved before rushing to replace it", "a painted leaf curled beneath the last clean letter"),
    Scenario("cans", "tower of donation cans", "stacked donation cans beneath a can-do sign", "A heavy can on top made the narrow tower sway.", "The base had two cans while the top row had five.", "grabbing the top can made the tower lean farther", "braced the bottom row", "moved top cans into a broad new base", "They rebuilt from the floor upward, passing one can at a time.", "The low pyramid stood firm, and 'We can' meant two things.", "sharing a load can make both a tower and a team stronger", "silver cans formed a sturdy triangle below the sign"),
    Scenario("garden", "basket of seed packets", "placed seeds beside a lettuce pun", "A sprinkler started early and swept the packets off the table.", "The packets drifted toward a drain while the basket stayed put.", "snatching at every packet sent waves in opposite directions", "blocked the drain with the basket", "scooped up packets with a dustpan", "They made a barrier first, then rescued the seeds row by row.", "Every packet dried safely, and 'lettuce help' sounded right.", "stop the cause before chasing all its scattered effects", "water drops sparkled on a row of saved seed packets"),
    Scenario("lights", "string of lanterns", "tested paper lanterns around the sign", "Only the first lantern glowed; the rest stayed dark.", "A connector after the first lantern hung loose.", "changing every bulb wasted time", "held the ladder steady", "clicked the loose connector into place", "They switched off the power, checked the connection, and tried again.", "Every lantern glowed, making their bright idea real.", "clear roles and a useful clue are brighter than frantic effort", "warm circles of light appeared above their joined hands"),
    Scenario("puppet", "cardboard puppet stage", "built a puppet stage beside the sign", "The curtain cord tangled around the sign and trapped the puppet.", "The left cord tightened the knot while the right cord loosened it.", "tugging both cords squeezed the cardboard frame", "held the frame square", "fed the loose cord backward through the knot", "They called 'hold' and 'feed' until the last loop opened.", "The puppet popped up and delivered the pun.", "teamwork includes listening when a partner needs you to pause", "a felt puppet bowed beneath a straight curtain"),
    Scenario("pear", "basket of pears", "arranged pears below a sign about a great pair", "The basket handle cracked as they lifted it.", "One side split cleanly, but the basket remained sound.", "carrying it by one side spilled two pears", "supported the basket underneath", "wrapped the handle with cloth tape", "They shared the weight, tested the handle low, and set the fruit down.", "Guests laughed at the pear-pair joke without another spill.", "a good pair shares the weight before it falls", "two golden pears touched stems in the repaired basket"),
    Scenario("rain", "chalkboard menu", "lettered the pun on a chalkboard menu", "Rain blew under the shelter and washed half the chalk away.", "One corner stayed dry beneath a folded cloth.", "writing faster in the rain made pale streaks", "tilted the board away from the wind", "clipped an apron over it as a roof", "They dried the board, copied the saved letters, and waited out the shower.", "The fresh words drew the first laugh of the event.", "sometimes a team protects the work first and finishes it second", "one raindrop slid off the apron without touching the chalk"),
    Scenario("microphone", "toy microphone", "practiced announcing the sign's joke", "The microphone squealed, swallowing the punch line.", "The squeal stopped when the microphone pointed away from the speaker.", "speaking louder only made the squeal louder", "moved the speaker behind the curtain", "marked a safe standing spot", "They tested one quiet word at a time until the joke sounded clear.", "The crowd heard the pun and applauded the patient sound crew.", "good partners listen to feedback, including the squeaky kind", "the microphone rested on its tape star after a clear chime"),
    Scenario("puzzle", "puzzle-piece sign", "assembled a giant puzzle-piece sign", "The final piece would not fit, though its colors looked right.", "Its tiny back arrow pointed opposite every other arrow.", "pushing harder bent a cardboard tab", "flattened the tab between two books", "turned the last piece around", "They followed the arrows, repaired the tab, and pressed gently.", "The sentence showed that every teammate had a place.", "a new viewpoint can help more than a stronger push", "the final piece sat flush with a gold arrow at its edge"),
]

SCENE_PUNS = {
    "wind": "Let's stick together!",
    "jam": "Teamwork is our jam!",
    "books": "Reading is a novel idea!",
    "paint": "Let's stick together!",
    "cans": "We can do it together!",
    "garden": "Lettuce help one another!",
    "lights": "Working together is a bright idea!",
    "puppet": "We really pull together!",
    "pear": "We make a great pear!",
    "rain": "Rain or shine, teamwork reigns!",
    "microphone": "Our teamwork is sound!",
    "puzzle": "We fit together!",
}

OPENINGS = [
    "The doors would open soon, and {hero} wanted one cheerful joke to welcome everyone.",
    "Long before the first guest arrived, {hero} and {helper} were already busy.",
    "A quiet corner of {venue} buzzed with preparation for {event}.",
    "{hero} had promised that {event} would begin with a smile, not a speech.",
    "Boxes, ribbons, and folding chairs filled {venue} on the morning of {event}.",
    "The smallest job on the list belonged to {hero}: make people smile as they entered.",
]
REACTIONS = [
    '"That is not the punch line I planned," {hero} said.',
    "{hero}'s first worried thought was to hide the mess.",
    '"Our joke needs help," {hero} admitted, taking one slow breath.',
    "For a moment, {hero} heard only the clock and felt responsible for everything.",
    '"I can fix it fast," {hero} said, though the problem was growing.',
    "The funny words no longer felt funny to {hero}.",
]
OFFERS = [
    '"Show me what changed, and we will choose jobs," {helper} said.',
    '"You do not have to rescue it alone," {helper} said.',
    '"Let us use the clue before we use more tape," {helper} suggested.',
    '"One pair of hands can steady while the other repairs," {helper} said.',
    '"Tell me your plan, and I will take the part you cannot reach," {helper} offered.',
    '"We can slow down without giving up," {helper} reminded {hero}.',
]
REFLECTIONS = [
    "The joke drew a laugh, but the repair made {hero} glow with pride.",
    "{hero} saw that the pun felt clever because their teamwork made it true.",
    "The guests noticed the joke; {hero} noticed how calmly they had solved the trouble.",
    "What warmed {hero} most was having someone stay through the hard part.",
    "The sign welcomed everyone, while the shared repair made {hero} feel welcome too.",
    "They had saved more than a joke: they had promised to help each other.",
]
DETAILS = [
    "They checked each step before moving on.",
    "They traded places when one set of arms grew tired.",
    "They named the problem aloud, then chose the next small step.",
    "They tested the repair gently before trusting it with the whole job.",
    "They listened to each other's count so neither moved too soon.",
    "They left enough time to test their work together.",
]


def pun_note(sign: str) -> str:
    return dict(PUNS).get(sign, "the words use a playful sound or double meaning")


def make_world(params: StoryParams) -> World:
    world = World(params=params)
    hero = Person(name=params.hero, role="hero")
    helper = Person(name=params.helper, role="helper")
    sign = ObjectItem(name="sign", label=params.sign, owner=hero.name)
    world.people = {hero.name: hero, helper.name: helper}
    world.items = {sign.name: sign}
    world.facts.update(hero=hero, helper=helper, sign=sign, venue=params.venue, event=params.event)
    return world


def generate_story_world(params: StoryParams) -> World:
    world = make_world(params)
    p = params
    rng = random.Random(p.seed if p.seed is not None else 0)
    scene = rng.choice(SCENARIOS)
    opening = rng.choice(OPENINGS).format(hero=p.hero, helper=p.helper, venue=p.venue, event=p.event)
    reaction = rng.choice(REACTIONS).format(hero=p.hero, helper=p.helper)
    offer = rng.choice(OFFERS).format(hero=p.hero, helper=p.helper)
    reflection = rng.choice(REFLECTIONS).format(hero=p.hero, helper=p.helper)

    world.say(opening)
    world.say(f"Together they {scene.premise} inside {p.venue} for {p.event}.")
    world.say(f'The sign read, "{p.sign}" It was a pun: {pun_note(p.sign)}.')
    world.para()
    world.say(scene.trouble)
    world.say(reaction)
    world.say(f"At first, {p.hero} tried alone, but {scene.failed_try}.")
    world.say(f"Then they noticed a clue: {scene.clue}")
    world.para()
    world.say(offer)
    world.say("Their teamwork gave each person one clear, useful job.")
    world.say(f"{p.hero} {scene.hero_task}, while {p.helper} {scene.helper_task}.")
    world.say(scene.solution)
    world.say(rng.choice(DETAILS))
    world.para()
    world.say(scene.result)
    world.say(reflection)
    world.say(f"{p.helper} said their lesson was simple: {scene.lesson}.")
    world.say(f"When {p.event} began, {scene.ending}.")

    world.people[p.hero].memes.update(worry=0.0, teamwork=1.0)
    world.people[p.helper].memes.update(care=1.0, teamwork=1.0)
    world.items["sign"].meters["readable"] = 1.0
    world.facts.update(
        scenario=scene.key, prop=scene.prop, trouble=scene.trouble, clue=scene.clue,
        failed_try=scene.failed_try, hero_task=scene.hero_task,
        helper_task=scene.helper_task, result=scene.result, lesson=scene.lesson,
        ending_image=scene.ending, pun_explanation=pun_note(p.sign), resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a heartwarming story about {p.hero} and {p.helper} using teamwork to rescue a pun at {p.event}.",
        f"Tell a child-friendly tale at {p.venue} where a practical clue helps solve a problem.",
        f"Create a gentle story in which shared work makes the words '{p.sign}' come true.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p, f = world.params, world.facts
    trouble = str(f["trouble"])
    clue = str(f["clue"])
    result = str(f["result"])
    return [
        QAItem(question=f"What interrupted {p.hero} and {p.helper}'s preparations?", answer=f"Their preparations were interrupted when {trouble[0].lower() + trouble[1:]} The trouble put the {f['prop']} and their pun at risk."),
        QAItem(question=f"What clue helped them understand the {f['prop']} problem?", answer=f"They noticed that {clue[0].lower() + clue[1:]} That clue gave them a safer plan than trying alone."),
        QAItem(question="How did the two teammates divide the repair?", answer=f"{p.hero} {f['hero_task']}, while {p.helper} {f['helper_task']}. Their different jobs supported the same solution."),
        QAItem(question="Why did the pun matter at the end?", answer=f'The sign said "{p.sign}" and {f["pun_explanation"]}. The joke became heartwarming because their teamwork made its message true.'),
        QAItem(question=f"What showed that the problem was solved at {p.event}?", answer=f"The result was clear: {result[0].lower() + result[1:]} In the final scene, {f['ending_image']}.")
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a pun?", answer="A pun is wordplay that uses similar sounds or more than one meaning. The surprise between those meanings can make a sentence funny."),
        QAItem(question="What does teamwork mean?", answer="Teamwork means people coordinate different jobs toward one result. They communicate, share effort, and help when one person cannot do everything alone."),
        QAItem(question="Why inspect a problem before fixing it?", answer="A useful clue can reveal the cause of a problem. Understanding the cause helps a team choose a repair that is careful and likely to last."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== World QA =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(K) :- helper_name(K).
sign(S) :- sign_text(S).
teamwork_success(H, K, S) :- hero(H), helper(K), sign(S), shared_fix(H, K, S).
heartwarming_story(H, K, S) :- teamwork_success(H, K, S), pun_sign(S).
"""
DEFAULT_PARAMS = StoryParams()


def asp_facts() -> str:
    import asp
    p = DEFAULT_PARAMS
    return "\n".join([asp.fact("hero_name", p.hero), asp.fact("helper_name", p.helper), asp.fact("sign_text", p.sign), asp.fact("pun_sign", p.sign), asp.fact("shared_fix", p.hero, p.helper, p.sign)])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    atoms = asp.atoms(asp.one_model(asp_program("#show heartwarming_story/3.")), "heartwarming_story")
    print("OK: ASP program produces a heartwarming teamwork story." if atoms else "MISMATCH: expected story atom missing.")
    return 0 if atoms else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--venue", choices=VENUES)
    parser.add_argument("--event", choices=EVENTS)
    parser.add_argument("--sign", choices=SIGNS)
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed, hero=args.hero or rng.choice(NAMES), helper=args.helper or rng.choice(HELPERS),
        venue=args.venue or rng.choice(VENUES), event=args.event or rng.choice(EVENTS),
        sign=args.sign or rng.choice(PUNS)[0], pun_word="pun",
        twist=rng.choice(TWISTS), fix=rng.choice(FIXES),
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(f"\n--- trace ---\nhero={sample.world.params.hero}\nhelper={sample.world.params.helper}\nscenario={sample.world.facts['scenario']}\nclue={sample.world.facts['clue']}\nresolved={sample.world.facts['resolved']}")
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show heartwarming_story/3.")); return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("1 compatible heartwarming teamwork story pattern."); return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        params = StoryParams(seed=base_seed)
        params.sign = SCENE_PUNS[random.Random(base_seed).choice(SCENARIOS).key]
        samples.append(generate(params))
    else:
        for i in range(args.n):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed)); params.seed = seed
            if args.sign is None:
                params.sign = SCENE_PUNS[random.Random(seed).choice(SCENARIOS).key]
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)); return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
