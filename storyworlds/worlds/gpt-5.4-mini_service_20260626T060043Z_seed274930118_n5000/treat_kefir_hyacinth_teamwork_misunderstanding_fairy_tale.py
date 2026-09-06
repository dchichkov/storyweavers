#!/usr/bin/env python3
"""
A fairy-tale storyworld about a shared treat, a jar of kefir, and a hyacinth
that causes a misunderstanding before teamwork sets it right.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Mira"
    helper: str = "Pip"
    elder: str = "Grandmother"
    creature: str = "mischievous sprite"
    place: str = "the cottage garden"
    treat: str = "honey cake"
    drink: str = "kefir"
    flower: str = "hyacinth"
    task: str = "make a treat for the spring feast"


@dataclass(frozen=True)
class Incident:
    title: str
    problem: str
    mistaken_belief: str
    clue: str
    failed_attempt: str
    cause: str
    helper_job: str
    hero_job: str
    creature_job: str
    repair: str
    lesson: str
    ending: str


INCIDENTS = [
    Incident(
        "The Vanished Ribbon",
        "the blue ribbon marking the finished tray had disappeared",
        "the {creature} believed the ribbon meant the whole tray was its promised gift",
        "a line of blue fibers led beneath the pantry door",
        "they accused the wind and shut every window, but the ribbon stayed missing",
        "the {creature} had carried the ribbon away to wrap one tiny thank-you parcel",
        "followed the fibers and listened before opening the pantry",
        "mixed a fresh kefir glaze while keeping the hyacinth safely beside the recipe card",
        "returned the ribbon and folded paper labels for every shared portion",
        "tied a new ribbon around the tray and made a separate parcel together",
        "A clue is kinder than an accusation, and a shared plan prevents hurt feelings.",
        "blue bows fluttered on many little parcels beneath the purple hyacinth",
    ),
    Incident(
        "The Sour-Sweet Note",
        "a note reading 'save the sour bowl' lay beside the kefir",
        "{helper} thought {elder} disliked the treat and wanted it thrown away",
        "the ink matched a label on a basket of berries",
        "they hid the bowl behind a flour sack, which only delayed the baking",
        "{elder} meant to save the tangy kefir for balancing the sweet berries",
        "matched the handwriting and fetched the berry basket",
        "asked what the note meant and measured the kefir into the mixture",
        "held the recipe open and rang a spoon when each step was complete",
        "rewrote the note as 'save this kefir for the berry mixture'",
        "Clear words are part of teamwork because helpers cannot follow a guess.",
        "one neat recipe card stood in a vase beside the fragrant hyacinth",
    ),
    Incident(
        "The Drooping Bell",
        "the hyacinth bent low just as the {treat} was carried to the cooling shelf",
        "{hero} thought the drooping flower was a fairy warning that the food had failed",
        "a dry ring showed where the flowerpot had missed its morning water",
        "they remade the topping, but the flower drooped lower",
        "the hyacinth was thirsty and had nothing to say about the safely baked {treat}",
        "brought water and moved the pot away from the warm oven",
        "checked the {treat} with the recipe timer instead of reading signs into the flower",
        "opened the curtain so the plant received gentle light",
        "watered the plant and judged the {treat} by real cooking clues",
        "Not every coincidence is a message; careful tests can untangle a misunderstanding.",
        "the revived flower bells rose beside the properly cooled {treat}",
    ),
    Incident(
        "The Cupboard Knock",
        "three knocks sounded inside the cupboard while the {treat} was baking",
        "{elder} feared someone had been secretly eating the feast supplies",
        "each knock came when the mill wheel turned outside",
        "they guarded the cupboard in silence, and the dough nearly rose too long",
        "a loose wooden spoon tapped the door whenever the wheel shook the wall",
        "timed the knocks and steadied the loose shelf",
        "checked the waiting {treat} and kept it from overbaking",
        "wedged a cork behind the spoon rack and admitted to an earlier cupboard visit",
        "secured the shelf, reset the timer, and finished the {treat} together",
        "Listening for a pattern can replace suspicion with a useful answer.",
        "the quiet cupboard reflected lamplight while the {treat} cooled safely",
    ),
    Incident(
        "The Borrowed Spoon",
        "the silver stirring spoon was gone when the kefir needed mixing",
        "{helper} assumed the {creature} had taken it to spoil the feast",
        "a dusting of potting soil crossed the sill toward the hyacinth bed",
        "they searched the {creature}'s pockets and found nothing but an acorn",
        "{elder} had borrowed the spoon to measure a safe scoop of plant food, then forgotten it outdoors",
        "followed the soil trail and washed the recovered spoon thoroughly",
        "found a clean wooden spoon so the cooking could continue safely",
        "sorted separate labels for garden tools and kitchen tools",
        "put the silver spoon away for washing and completed the treat with clean equipment",
        "Good teammates correct a mix-up without making the wrongly blamed person feel small.",
        "two clearly labeled hooks gleamed above a tray of warm {treat} portions",
    ),
    Incident(
        "The Empty Place Card",
        "one blank place card sat beside the feast table",
        "the {creature} believed the blank card meant it had not been invited",
        "a smear of kefir hid faint silver letters on the card",
        "it rolled the hyacinth pot in front of the card and prepared to leave",
        "a tipped tasting cup had covered the {creature}'s carefully written name",
        "dabbed the card dry and read the first shining letter",
        "made a replacement card and set the treat safely away from the table edge",
        "polished the little bell that would call everyone to supper",
        "restored the name card and rearranged the crowded table together",
        "Before deciding we are unwanted, we can ask what an unclear sign really means.",
        "the {creature}'s silver name shone between the hyacinth and its own small plate",
    ),
    Incident(
        "The Purple Footprints",
        "purple marks crossed the floor from the hyacinth to the covered treat",
        "{hero} thought muddy feet had touched the feast food",
        "the marks were dry pollen circles with a clean gap around the covered plate",
        "they began another treat before checking beneath the cloth",
        "a bee-sized fairy had brushed loose pollen from the flower while flying over the floor",
        "mapped the circles and showed that none reached the food",
        "inspected the cover and stored the kefir back in the cool pantry",
        "swept the pollen into a garden bowl and apologized for the alarm",
        "cleaned the floor, kept the treat covered, and invited the fairy to explain",
        "Evidence tells us what happened; fear alone only tells us what might have happened.",
        "clean floorboards curved around an untouched treat beneath its glass cover",
    ),
    Incident(
        "The Missing Slice",
        "a slice-shaped gap appeared in the cooling treat before the feast",
        "{elder} believed an impatient guest had helped themselves",
        "crumbs stopped at a small parcel labeled for the bridge keeper",
        "everyone counted plates twice while the parcel waited unnoticed",
        "{hero} had cut the promised thank-you portion early and forgotten to explain",
        "read the parcel label aloud and checked it against the guest list",
        "owned the mistake and told the group why the slice had been set aside",
        "added a painted hyacinth card and carried the parcel after supper",
        "marked promised portions on a shared list before arranging the remaining slices",
        "Teamwork includes telling others what we have already done.",
        "one wrapped slice rested by the door while the full table welcomed every guest",
    ),
    Incident(
        "The Warm Kefir",
        "the kefir jar felt warmer than expected when baking began",
        "{helper} assumed the {creature} had left it by the stove carelessly",
        "a bright rectangle on the shelf showed where morning sunlight had moved",
        "they scolded the {creature} before asking who had used the jar last",
        "the sunbeam had crossed the shelf after {elder} set the jar there",
        "moved the jar to the cool pantry and checked it with {elder} before using it",
        "chose a fresh chilled jar for the treat and apologized for the quick blame",
        "hung a little curtain to shade the shelf",
        "discarded the doubtful jar, labeled the safe storage place, and baked together",
        "Food safety needs careful action, while fairness needs careful questions.",
        "a blue curtain shaded the cool shelf as the fresh treat left the oven",
    ),
    Incident(
        "The Two Feast Bells",
        "a bell rang early and sent guests toward a table that was not ready",
        "{hero} and {helper} believed the {creature} had rung it as a prank",
        "the sound came again when a hyacinth stem tapped a tiny glass charm",
        "they moved the feast bell, yet another silvery chime followed",
        "the breeze was swinging the flower against a look-alike charm",
        "compared both sounds and tied the charm away from the stem",
        "covered the treat and calmly guided the early guests to the garden",
        "made a picture sign showing which bell truly announced supper",
        "separated the two bells and agreed who would ring the real one",
        "When signals are confusing, teammates can compare them and make the system clearer.",
        "the true feast bell rang once above a table bright with candles",
    ),
    Incident(
        "The Swapped Jugs",
        "two identical blue jugs stood beside the mixing bowl",
        "{hero} believed {helper} had poured water instead of kefir into the mixture",
        "one jug had a cool white drop on its handle and the mixture smelled gently tangy",
        "they argued over whose memory was right while the oven warmed",
        "the labels had turned toward the wall, but the correct kefir had already been used",
        "turned both labels forward and checked the remaining amounts",
        "tested the mixture against the recipe and withdrew the accusation",
        "painted a hyacinth on the kefir jug so it could be recognized at a glance",
        "finished the {treat}, then stored the clearly marked jugs on separate shelves",
        "A shared check can solve a disagreement better than two competing memories.",
        "the flower-painted jug stood beside the evenly baked {treat}",
    ),
    Incident(
        "The Crumb Trail Promise",
        "a crumb trail led from the treat table into the moonlit garden",
        "the {creature} thought the cooks had begun the feast without it",
        "every crumb was square and tasted of plain travel bread, not the round sweet treat",
        "it hid the serving cloth in disappointment, making everyone think the cloth was stolen",
        "{elder} had carried travel bread to a tired messenger and dropped crumbs on the path",
        "compared the two breads and invited the {creature} to ask about the trail",
        "explained the messenger's need and listened to why the cloth had been hidden",
        "returned the cloth, shook it clean outdoors, and helped set every place",
        "replaced guesses with apologies and prepared an extra kefir cup for the messenger",
        "Sharing with one person does not exclude another, but hidden actions still need honest repair.",
        "a lantern-lit path joined the messenger's bench to the welcoming feast table",
    ),
]

OPENINGS = [
    "At the edge of an old kingdom",
    "Beyond a gate braided with ivy",
    "On the morning of the village feast",
    "Where the orchard met the castle road",
    "Under a hill said to shelter kind fairies",
    "Before the moon lanterns were lit",
    "In a cottage with a blue-tiled hearth",
    "On a bright day in the smallest royal garden",
]

QUESTIONS = [
    "Let us ask what each of us actually saw.",
    "A guess is not a clue. What can we test?",
    "We are teammates, so we should listen before deciding.",
    "Let us follow the evidence from the beginning.",
    "No one should be blamed until the pieces fit.",
    "We can mend the problem and the hurt feelings together.",
    "Tell us your part, and we will tell you ours.",
    "What changed, and what only seemed to change?",
]

TEAMWORK_IMAGES = [
    "They divided the work by naming each job aloud.",
    "They made a three-step plan and checked each step together.",
    "One watched, one worked, and one read the instructions.",
    "They traded tasks whenever another pair of hands was needed.",
    "They laid the clues in a row before choosing their next action.",
    "They repeated the plan until everyone could explain it.",
    "They worked quietly first, then compared what each had learned.",
    "They used a chalk list so no useful task was forgotten.",
]

ENDING_PERSPECTIVES = [
    "The youngest guest remembered the honest apology most clearly.",
    "The elder later praised the moment when guessing gave way to listening.",
    "The helper kept the useful clue as a reminder to test first.",
    "The hero remembered that repairing trust mattered as much as repairing the feast.",
    "The creature discovered that asking a question took more courage than hiding a mistake.",
    "The cooks added the clearer procedure to their book of feast-day wisdom.",
    "The neighbors retold the tale whenever a rumor began to outrun the facts.",
    "The team agreed that every future plan would include a chance to ask questions.",
    "The old kingdom gained a small new custom: clues before blame.",
    "The feast became famous not for perfection, but for the repair everyone made together.",
    "The next morning, each teammate could explain both the mistake and its remedy.",
    "Long afterward, the final peaceful picture mattered more than the earlier confusion.",
]


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amt: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amt

    def add_meme(self, key: str, amt: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amt


@dataclass
class World:
    params: StoryParams
    hero: Entity
    helper: Entity
    elder: Entity
    creature: Entity
    place: str
    treat_ready: bool = False
    misunderstanding: bool = False
    teamwork: bool = False
    flower_used: bool = False
    kefir_spilled: bool = False
    incident: Optional[Incident] = None
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale world of treat, kefir, and hyacinth.")
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
    ap.add_argument("--creature")
    ap.add_argument("--place")
    ap.add_argument("--treat")
    ap.add_argument("--kefir")
    ap.add_argument("--flower")
    ap.add_argument("--task")
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
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(["Mira", "Nina", "Tara", "Lena"]),
        helper=args.helper or rng.choice(["Pip", "Nico", "Bram", "Sera"]),
        elder=args.elder or rng.choice(["Grandmother", "Old Rowan", "Queen Elin", "the baker"]),
        creature=args.creature or rng.choice(["mischievous sprite", "small goblin", "young dragon"]),
        place=args.place or rng.choice(["the cottage garden", "the mossy well", "the moonlit kitchen"]),
        treat=args.treat or rng.choice(["honey cake", "berry tart", "sweet bun"]),
        drink=args.kefir or "kefir",
        flower=args.flower or "hyacinth",
        task=args.task or "make a treat for the spring feast",
    )


def _maybe_raise_invalid(params: StoryParams) -> None:
    bad_words = {"forbidden", "poison", "broken"}
    if params.treat.lower() in bad_words or params.drink.lower() in bad_words:
        raise StoryError("The fairy tale needs a gentle treat and a wholesome drink.")
    if not params.flower:
        raise StoryError("A hyacinth must be present for the misunderstanding to bloom.")


def _stable_rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0x5A17F4)
    key = "|".join(
        [params.hero, params.helper, params.elder, params.creature, params.place,
         params.treat, params.drink, params.flower, params.task]
    )
    seed = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")
    return random.Random(seed)


def _ground_incident(incident: Incident, params: StoryParams) -> Incident:
    values = {
        "hero": params.hero,
        "helper": params.helper,
        "elder": params.elder,
        "creature": params.creature,
        "treat": params.treat,
    }
    updates = {
        name: getattr(incident, name).format(**values)
        for name in incident.__dataclass_fields__
        if name != "title"
    }
    return replace(incident, **updates)


def _sentence_name(name: str) -> str:
    return name[:1].upper() + name[1:]


def _setup(world: World, opening: str) -> None:
    p = world.params
    world.say(
        f"{opening}, {p.hero} and {p.helper} worked near {p.place}. This was a fairy-tale "
        f"country, but its best magic was still patience, truth, and willing hands."
    )
    world.say(
        f"They had promised {p.elder} they would {p.task}: a {p.treat} made with {p.drink}. "
        f"A fragrant {p.flower} stood nearby as a table decoration, safely apart from the food."
    )


def _misunderstanding(world: World, incident: Incident) -> None:
    p = world.params
    world.para()
    world.misunderstanding = True
    world.creature.add_meme("curiosity", 1)
    world.elder.add_meme("worry", 1)
    world.hero.add_meme("hope", 1)
    world.say(f"The day's trouble earned a name: {incident.title}. It began when {incident.problem}.")
    world.say(f"In the confusion, {incident.mistaken_belief}.")
    world.say(f"At first, {incident.failed_attempt}. That did not solve anything, and feelings tightened like knotted string.")


def _teamwork(world: World, incident: Incident, question: str, method: str) -> None:
    p = world.params
    world.para()
    world.teamwork = True
    world.hero.add_meme("resolve", 1)
    world.helper.add_meme("resolve", 1)
    world.say(f"{p.hero} took a breath and said to {p.helper}, '{question}'")
    world.say(f"{method} Their best clue was this: {incident.clue}.")
    world.say(
        f"Together they discovered the real cause: {incident.cause}. The misunderstanding "
        f"began to loosen as soon as everyone could see the same evidence."
    )
    world.say(
        f"For the repair, {p.helper} {incident.helper_job}; {p.hero} {incident.hero_job}; and "
        f"the {p.creature} {incident.creature_job}."
    )


def _resolution(world: World, incident: Incident, perspective: str) -> None:
    p = world.params
    world.para()
    world.treat_ready = True
    world.flower_used = True
    world.kefir_spilled = False
    world.say(f"Their teamwork worked: they {incident.repair}.")
    world.say(
        f"The {p.treat}, with its wholesome {p.drink}, was ready at last. The {p.flower} remained "
        f"a lovely decoration rather than something to eat, and everyone received a fair share."
    )
    world.say(f"{_sentence_name(p.elder)} said, '{incident.lesson}'")
    world.say(
        f"When the feast ended, {incident.ending}. {perspective} That was how a "
        f"misunderstanding became a wiser fairy tale."
    )


def tell(params: StoryParams) -> World:
    _maybe_raise_invalid(params)
    hero = Entity(params.hero, "hero")
    helper = Entity(params.helper, "helper")
    elder = Entity(params.elder, "elder")
    creature = Entity(params.creature, "creature")
    world = World(params=params, hero=hero, helper=helper, elder=elder, creature=creature, place=params.place)
    rng = _stable_rng(params)
    incident = _ground_incident(rng.choice(INCIDENTS), params)
    world.incident = incident
    _setup(world, rng.choice(OPENINGS))
    _misunderstanding(world, incident)
    _teamwork(world, incident, rng.choice(QUESTIONS), rng.choice(TEAMWORK_IMAGES))
    _resolution(world, incident, rng.choice(ENDING_PERSPECTIVES))
    world.facts = {
        "hero": hero,
        "helper": helper,
        "elder": elder,
        "creature": creature,
        "place": params.place,
        "treat": params.treat,
        "drink": params.drink,
        "flower": params.flower,
        "incident": incident.title,
        "problem": incident.problem,
        "clue": incident.clue,
        "cause": incident.cause,
        "repair": incident.repair,
        "lesson": incident.lesson,
        "ending": incident.ending,
        "misunderstanding": world.misunderstanding,
        "teamwork": world.teamwork,
        "resolved": world.treat_ready,
    }
    return world


ASP_RULES = r"""
hero(X) :- hero_name(X).
helper(X) :- helper_name(X).
misunderstanding :- sees(creature, flower, kefir), not knows_shared_treat(creature).
teamwork :- asks_help(hero), helps(helper), mends_treat(hero, helper).
resolved :- teamwork, misunderstanding.
#show misunderstanding/0.
#show teamwork/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero_name", "Mira"),
        asp.fact("helper_name", "Pip"),
        asp.fact("sees", "creature", "flower", "kefir"),
        asp.fact("asks_help", "hero"),
        asp.fact("helps", "helper"),
        asp.fact("mends_treat", "hero", "helper"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception:
        print("ASP verification unavailable: clingo helper not installed.")
        return 1
    model = asp.one_model(asp_program("#show misunderstanding/0.\n#show teamwork/0.\n#show resolved/0."))
    atoms = {str(a) for a in model}
    expected = {"misunderstanding", "teamwork", "resolved"}
    if atoms >= expected:
        print("OK: ASP twin produces the expected fairy-tale state.")
        return 0
    print("MISMATCH: ASP twin did not reach the expected state.")
    return 1


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a short fairy tale about {p.hero}, {p.helper}, and a shared {p.treat}.",
        f"Tell a gentle story where {p.drink} and a {p.flower} lead to a misunderstanding, then teamwork fixes it.",
        f"Write a child-friendly story set near {p.place} that ends with everyone sharing the treat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    incident = world.incident
    assert incident is not None
    return [
        QAItem(
            question=f"What trouble interrupted {p.hero} and {p.helper}'s work?",
            answer=f"{incident.problem.capitalize()}. That problem led someone to make a mistaken guess.",
        ),
        QAItem(
            question="What clue helped the team understand what had really happened?",
            answer=f"They noticed that {incident.clue}. It pointed them toward the real cause instead of a quick accusation.",
        ),
        QAItem(
            question=f"How did {p.hero}, {p.helper}, and the {p.creature} use teamwork?",
            answer=(
                f"{p.helper} {incident.helper_job}; {p.hero} {incident.hero_job}; and the "
                f"{p.creature} {incident.creature_job}. Their different jobs supported one repair."
            ),
        ),
        QAItem(
            question="What did the characters learn from the misunderstanding?",
            answer=incident.lesson,
        ),
        QAItem(
            question="What final image showed that the trouble was resolved?",
            answer=f"At the end, {incident.ending}. The concrete scene showed that the team had repaired both the problem and the feast.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together to do a job that is easier or better with help.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing and gets confused.",
        ),
        QAItem(
            question=f"What is kefir?",
            answer=f"Kefir is a tangy, drinkable dairy food that people can use in recipes or drink cold.",
        ),
        QAItem(
            question=f"What is a hyacinth?",
            answer=f"A hyacinth is a fragrant flower with clustered blooms, often purple, pink, or blue.",
        ),
        QAItem(
            question=f"What is a treat?",
            answer=f"A treat is a special food that feels joyful or festive, like a sweet {p.treat}.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in [world.hero, world.helper, world.elder, world.creature]:
        lines.append(f"{ent.kind}: {ent.name} meters={ent.meters} memes={ent.memes}")
    lines.append(f"state: misunderstanding={world.misunderstanding} teamwork={world.teamwork} resolved={world.treat_ready}")
    return "\n".join(lines)


CURATED = [
    StoryParams(hero="Mira", helper="Pip", elder="Grandmother", creature="small goblin", place="the cottage garden", treat="honey cake", drink="kefir", flower="hyacinth"),
    StoryParams(hero="Lena", helper="Bram", elder="Old Rowan", creature="mischievous sprite", place="the moonlit kitchen", treat="berry tart", drink="kefir", flower="hyacinth"),
]


def asp_verify_available() -> bool:
    try:
        import clingo  # noqa: F401
        return True
    except Exception:
        return False


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/0.\n#show teamwork/0.\n#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        if not asp_verify_available():
            print("ASP mode unavailable: clingo is not installed.")
            return
        import asp
        model = asp.one_model(asp_program("#show misunderstanding/0.\n#show teamwork/0.\n#show resolved/0."))
        print("ASP model:", ", ".join(sorted(str(a) for a in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.helper} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
