#!/usr/bin/env python3
"""
A small fable-like storyworld about a salon visit, a bushed character, stylish
pride, dialogue, and reconciliation.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Salon:
    name: str
    kind: str = "salon"
    tidy: bool = True
    chairs: int = 2


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, salon: Salon) -> None:
        self.salon = salon
        self.entities: dict[str, Entity] = {}
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


SALONS = {
    "salon": Salon(name="the little salon", tidy=True, chairs=3),
}

NAMES = ["Pip", "Mina", "Ivy", "Tari", "Luna", "Nico", "Sage", "Milo"]
TRAITS = ["stylish", "careful", "bright", "kind", "gentle", "proud"]

INCIDENTS = [
    {
        "key": "quiet_corner",
        "premise": "a costume-day line curled past the welcome mat",
        "conflict": "the lively chatter left the bushed visitor unable to explain what they needed",
        "mistake": "mistook the silence for dislike and began putting away the scarf samples",
        "clue": "a small card in the visitor's paw read, 'May I have a quiet minute first?'",
        "action": "moved two chairs behind a folding screen and brought a cup of water",
        "repair": "made a quiet waiting corner and let the visitor choose when to continue",
        "gift": "a soft green scarf",
        "lesson": "rest can be part of welcome",
        "ending": "the green scarf hung beside the new QUIET CORNER sign",
    },
    {
        "key": "mixed_tags",
        "premise": "three cape orders waited on hooks before the moonlight parade",
        "conflict": "the name tags had slipped, and each friend thought the other had taken the stylish cape",
        "mistake": "reached for the shiniest cape before checking its stitched initials",
        "clue": "a silver thread on one tag matched the hem of the smallest cape",
        "action": "laid the capes on a clean table and compared every tag with the order book",
        "repair": "returned each cape to its owner and added tied-on tags that could not slide",
        "gift": "a starry blue cape",
        "lesson": "evidence settles a quarrel better than guessing",
        "ending": "three correctly tagged capes fluttered together beneath the parade lanterns",
    },
    {
        "key": "missing_button",
        "premise": "a brass button vanished from a borrowed vest minutes before a recital",
        "conflict": "one friend accused the other of losing it while hurrying through the salon",
        "mistake": "searched through a visitor's bag without first asking permission",
        "clue": "a round print in the dust ended beneath the rolling ribbon cart",
        "action": "apologized, asked permission to move the cart, and used a flashlight from the floor",
        "repair": "found the button and asked the salon tailor to sew it on securely",
        "gift": "a plum-colored vest",
        "lesson": "privacy still matters when time feels short",
        "ending": "the rescued button winked under the recital lights",
    },
    {
        "key": "rainy_ribbons",
        "premise": "a sudden rain blew through an open transom above the ribbon shelf",
        "conflict": "the bushed friend felt blamed when damp ribbons spotted a display",
        "mistake": "called the mess careless before noticing the drops on the window ledge",
        "clue": "a trail of rain dots ran from the transom, not from either friend's paws",
        "action": "closed the transom, marked the wet floor, and asked an adult attendant for dry cloths",
        "repair": "dried the shelf together and moved the ribbons into covered boxes",
        "gift": "a sunny yellow ribbon",
        "lesson": "look for the cause before placing blame",
        "ending": "yellow ribbon bows gleamed safely behind clear box lids",
    },
    {
        "key": "mirror_message",
        "premise": "a kind note on the salon mirror appeared smudged and unreadable",
        "conflict": "each friend believed the other had erased the message",
        "mistake": "answered the suspected insult with a sharp voice",
        "clue": "tiny damp circles matched the mist from a nearby plant mister",
        "action": "tested one corner with the attendant and read the remaining letters aloud",
        "repair": "rewrote the note on paper and apologized for the accusation",
        "gift": "a card saying STYLE IS CHOOSING WHAT FEELS LIKE YOU",
        "lesson": "a blurred message is not proof of an unkind act",
        "ending": "the new card stood crisp beside the mirror while both friends laughed at their reflections",
    },
    {
        "key": "shared_stool",
        "premise": "only one low footstool remained during a busy story-hour fitting",
        "conflict": "both tired friends needed it and began tugging from opposite sides",
        "mistake": "insisted that arriving first mattered more than hearing why the other needed help",
        "clue": "the appointment board showed a long fitting for one friend and a short pin check for the other",
        "action": "stopped pulling, listened, and divided the appointment into two timed turns",
        "repair": "shared the stool and asked the attendant to bring a spare cushion",
        "gift": "matching leaf-shaped clips",
        "lesson": "fair sharing begins with listening to different needs",
        "ending": "the two leaf clips rested side by side on the appointment card",
    },
    {
        "key": "surprise_choice",
        "premise": "a surprise makeover banner dropped before anyone asked what the guest wanted",
        "conflict": "the bushed guest froze because the planned style did not feel like them",
        "mistake": "defended the surprise instead of noticing the guest's quiet no",
        "clue": "the guest kept pointing to a simple comb-and-scarf picture in the style book",
        "action": "took down the banner and asked, 'What would feel comfortable today?'",
        "repair": "canceled the makeover and arranged only the simple, chosen scarf",
        "gift": "a plain red scarf",
        "lesson": "a stylish choice belongs to the person wearing it",
        "ending": "the unused banner was folded away while the red scarf danced at the doorway",
    },
    {
        "key": "borrowed_brooch",
        "premise": "a sparkling brooch was promised for two different costumes",
        "conflict": "the double promise made both friends feel tricked",
        "mistake": "tried to decide whose costume looked more deserving",
        "clue": "two reservation cards carried the same brooch number and the same clerk's stamp",
        "action": "brought both cards to the attendant and asked for an equal solution",
        "repair": "used the brooch for the earlier portrait, then loaned a matching salon pin for the play",
        "gift": "a moon-shaped salon pin",
        "lesson": "people deserve fair promises, not judgments about their looks",
        "ending": "the brooch and moon pin shone in two different photographs on the salon wall",
    },
    {
        "key": "snagged_scarf",
        "premise": "a favorite scarf caught on a loose wicker thread beside the waiting chair",
        "conflict": "the owner thought a friend had pulled it on purpose",
        "mistake": "yanked the scarf free and made the small snag longer",
        "clue": "one blue fiber remained looped around the broken wicker end",
        "action": "stopped pulling, photographed the clue, and called the attendant",
        "repair": "let the salon tailor mend the scarf while the attendant covered the damaged chair",
        "gift": "a mended ocean-blue scarf",
        "lesson": "pause before a hurried action makes damage worse",
        "ending": "the smooth blue scarf curled over a chair marked READY AFTER REPAIR",
    },
    {
        "key": "wrong_compliment",
        "premise": "the salon hosted a compliment circle before its friendship fair",
        "conflict": "a comment about looking less tired made the bushed friend feel watched instead of welcomed",
        "mistake": "argued that a compliment must be kind simply because it sounded cheerful",
        "clue": "the friend's crossed-out card replaced LOOKS with the words PATIENT and HELPFUL",
        "action": "listened without interrupting and asked what kind of praise felt comfortable",
        "repair": "apologized and praised the friend's patience in organizing the ribbon shelf",
        "gift": "a badge reading THOUGHTFUL HELPER",
        "lesson": "kind words honor what someone does and how they wish to be seen",
        "ending": "the helper badge glowed above a perfectly sorted rainbow of ribbons",
    },
    {
        "key": "lost_sketch",
        "premise": "a hand-drawn style plan disappeared before the fable festival",
        "conflict": "the tired artist believed a friend had rejected the design",
        "mistake": "started a replacement without asking what mattered in the original",
        "clue": "purple chalk dust crossed the floor toward the salon's paper-recycling tray",
        "action": "followed the dust, asked the attendant to check the tray, and found the folded sketch",
        "repair": "flattened the sketch under clean books and let the artist direct every choice",
        "gift": "a paper crown with purple stars",
        "lesson": "help works best when it follows the creator's wishes",
        "ending": "the saved sketch stood beside its finished purple-star crown",
    },
    {
        "key": "closing_bell",
        "premise": "the salon's closing bell rang halfway through two friends' festival preparations",
        "conflict": "one wanted to rush while the bushed friend needed to stop and rest",
        "mistake": "treated finishing on time as more important than the friend's clear limit",
        "clue": "the booking card included a free return visit the following morning",
        "action": "read the card, packed the accessories carefully, and chose rest over rushing",
        "repair": "returned after breakfast and finished the chosen styles without hurry",
        "gift": "two comfortable festival sashes",
        "lesson": "resting is wiser than racing past a person's limit",
        "ending": "two bright sashes waved at the festival as the salon bell chimed behind them",
    },
]

OPENINGS = [
    "By the time the salon clock chimed,",
    "On the morning of the neighborhood festival,",
    "Just after the salon door opened,",
    "While colored ribbons turned in the window,",
    "Near the end of a long afternoon,",
    "As rain tapped the salon awning,",
    "Before the little salon's busiest hour,",
    "When the mirror lights blinked on,",
    "During a quiet visit to the salon,",
    "As the last appointment card was pinned up,",
]

REFLECTIONS = [
    "Being tired did not make anyone less stylish; it simply meant that rest and patience mattered.",
    "No mirror could measure kindness, consent, or courage, which were the qualities the friends admired.",
    "They agreed that style was personal, while respect was something friends owed one another.",
    "The salon could offer choices, but nobody had to change their appearance to deserve welcome.",
    "A neat accessory could be fun, yet listening was what repaired their friendship.",
    "They learned to ask before helping and to believe a friend's answer about their own comfort.",
    "Neither friend needed to look energetic to be valued; honest words were enough.",
    "Their reconciliation began when winning the argument stopped mattering more than understanding it.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like salon storyworld.")
    ap.add_argument("--setting", choices=SALONS.keys())
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    setting = args.setting or "salon"
    hero_name = args.name or rng.choice(NAMES)
    friend_name = args.friend or rng.choice([n for n in NAMES if n != hero_name])
    return StoryParams(setting=setting, hero_name=hero_name, friend_name=friend_name)


def tell(params: StoryParams) -> World:
    salon_template = SALONS[params.setting]
    world = World(
        Salon(
            name=salon_template.name,
            tidy=salon_template.tidy,
            chairs=salon_template.chairs,
        )
    )
    hero = world.add(Entity(id=params.hero_name, kind="character", type="rabbit", traits=["stylish"]))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="fox", traits=["bushed"]))
    rng = random.Random(params.seed if params.seed is not None else 0)
    incident = rng.choice(INCIDENTS)
    opening = rng.choice(OPENINGS)
    reflection = rng.choice(REFLECTIONS)
    concern = rng.choice(
        [
            "I think you decided before hearing me",
            "I needed you to ask, not guess",
            "I am tired, but I can still choose for myself",
            "That did not feel fair from my side",
            "Please listen to what actually happened",
            "I want help, though not that kind of help",
            "I would rather solve this with you than argue",
            "Can we slow down and look at the clue together",
        ]
    )
    apology = rng.choice(
        [
            "I am sorry I guessed instead of listening",
            "I was wrong to rush you",
            "I made the conflict bigger, and I want to repair it",
            "You were clear; I should have respected your answer",
            "I blamed you before checking the evidence",
            "I meant to help, but I did not ask what help you wanted",
            "I care more about our friendship than being right",
            "Thank you for telling me. I will do this differently",
        ]
    )
    agreement = rng.choice(
        [
            "ask first, listen fully, then act",
            "pause, check the evidence, and choose together",
            "make room for rest as well as celebration",
            "describe the problem without judging a person",
            "let each wearer define what stylish means to them",
            "repair the mistake and change the rule that allowed it",
            "use calm words even when the clock feels loud",
            "protect comfort, privacy, and friendship at the same time",
        ]
    )

    hero.memes.update(pride=1, impatience=1)
    friend.memes.update(weariness=1, hurt=1)
    friend.meters["tired"] = 1
    world.salon.tidy = incident["key"] not in {"rainy_ribbons", "snagged_scarf"}

    world.say(
        f"{opening} {hero.id}, a stylish rabbit, was helping at {world.salon.name}. "
        f"{friend.id}, a fox who was bushed after a long day, arrived hoping for a peaceful visit."
    )
    world.say(f"That was when {incident['premise']}.")
    world.para()

    world.say(
        f"A conflict began because {incident['conflict']}. {hero.id} {incident['mistake']}."
    )
    world.say(f"'{concern},' {friend.id} said.")
    world.say(
        f"{hero.id} started to answer quickly, then noticed this clue: {incident['clue']}."
    )
    world.para()

    world.say(f"'{apology},' {hero.id} said. 'May we work on it together?'")
    world.say(f"{friend.id} nodded, and {hero.id} {incident['action']}.")
    world.say(
        f"Instead of trying to change anyone's looks, the friends {incident['repair']}. "
        f"They included {incident['gift']} only after {friend.id} said the choice felt comfortable and welcome."
    )
    world.para()

    friend.memes.update(hurt=0, trust=1, reconciled=1)
    hero.memes.update(impatience=0, kindness=1, reconciled=1)
    world.say(
        f"Their reconciliation was more than saying sorry: they agreed to {agreement}. "
        f"The fable's lesson was that {incident['lesson']}."
    )
    world.say(reflection)
    world.say(f"At the end, {incident['ending']}.")

    world.facts.update(
        hero=hero,
        friend=friend,
        salon=world.salon,
        incident=incident,
        concern=concern,
        apology=apology,
        agreement=agreement,
        reflection=reflection,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    incident = world.facts["incident"]
    return [
        f"Write a child-friendly fable set in a salon where {incident['premise']}.",
        f"Tell a dialogue-rich story about two friends who reconcile by learning to {world.facts['agreement']}.",
        f"Write a gentle salon fable whose lesson is that {incident['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    incident = f["incident"]
    return [
        QAItem(
            question=f"What started the conflict between {hero.id} and {friend.id}?",
            answer=f"The conflict began because {incident['conflict']}. {hero.id} then {incident['mistake']}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} reconsider the first guess?",
            answer=f"{hero.id} noticed that {incident['clue']}. That evidence showed why a slower, fairer response was needed.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} repair the problem?",
            answer=f"They {incident['repair']}. Their reconciliation also included an apology and an agreement to {f['agreement']}.",
        ),
        QAItem(
            question=f"Why did the story call {friend.id} bushed?",
            answer=f"{friend.id} was very tired after a long day. Being bushed did not make {friend.id} less worthy or less stylish.",
        ),
        QAItem(
            question="What lesson did the friends carry out of the salon?",
            answer=f"They learned that {incident['lesson']}. The ending showed that {incident['ending']}, a concrete sign that their repair lasted.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a salon?",
            answer="A salon is a place where people or animals go to have hair, fur, or style cared for.",
        ),
        QAItem(
            question="What does bushed mean?",
            answer="Bushed means very tired, as if a long day has worn you out.",
        ),
        QAItem(
            question="What does stylish mean?",
            answer="Stylish describes a way of presenting yourself that feels expressive or well chosen. It is personal, and it does not decide anyone's worth.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when friends who were upset make peace and feel friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("\n== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
salon(salon).
style_word(stylish).
feeling(bushed).
feature(dialogue).
feature(reconciliation).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", "salon"),
        asp.fact("style_word", "stylish"),
        asp.fact("feeling", "bushed"),
        asp.fact("feature", "dialogue"),
        asp.fact("feature", "reconciliation"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show feature/1."))
    feats = set(asp.atoms(model, "feature"))
    want = {("dialogue",), ("reconciliation",)}
    if feats == want:
        print("OK: ASP facts match Python story features.")
        return 0
    print("Mismatch in ASP verification.")
    return 1


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
        print(asp_program("#show feature/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show feature/1."))
        feats = sorted(set(asp.atoms(model, "feature")))
        print(feats)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        sample = generate(StoryParams(setting="salon", hero_name="Pip", friend_name="Mina"))
        samples = [sample]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
