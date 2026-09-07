#!/usr/bin/env python3
"""Library Words: a misunderstood request changes where a book, page, or voice goes.

Keep each belief on its speaker. A reply can pass it to the listener, but only
an executed action moves the book or marks the page. QA comes from those events.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    speaker: str = ""
    listener: str = ""
    revealed: str = ""
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Mia"
    friend: str = "Ben"
    problem: str = "place"
    solution: str = "bookmark"
    approach: str = "ask"
    item: str = "boat"
    seed: int = 777


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(id="hero", label=params.hero, kind="character",
                           memes={"frustration": 1.0, "trust": 0.5}),
            "friend": Entity(id="friend", label=params.friend, kind="character",
                             memes={"frustration": 0.5, "trust": 0.5}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(kind=kind, text=text, question=question,
                                  cause=cause, result=result, state=self.snapshot()))

    def say(self, speaker: str, text: str, *, to="", reveal="", tag="said"):
        actor = self.entities[speaker]
        if reveal:
            if not to or reveal not in actor.beliefs:
                raise StoryError("A speaker cannot pass on information they do not know.")
            self.entities[to].beliefs[reveal] = actor.beliefs[reveal]
        if text.endswith("?") and tag == "said":
            tag = "asked"
        if text.endswith("."):
            text = text[:-1] + ","
        self.history.append(Event(kind="speech", text=f'"{text}" {actor.label} {tag}.',
                                  speaker=speaker, listener=to, revealed=reveal,
                                  state=self.snapshot()))

    def agree(self):
        for key in ("hero", "friend"):
            self.entities[key].memes.update(frustration=0.0, trust=1.0)

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params, story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[QAItem(question=event.question, answer=f"{event.cause} {event.result}")
                      for event in self.history if event.question],
            world_qa=[], world=self,
        )


NAMES = ("Mia", "Ben", "Noor", "Sam", "Lily", "Theo")
APPROACHES = ("ask", "guess")

PROMPT = "Write a dialogue-rich children's story about two friends clearing up a misunderstanding in a library."
PROBLEMS = {"place": "remember_page", "return": "recover_book", "quiet": "be_heard"}
SOLUTIONS = {"bookmark": "remember_page", "fetch": "recover_book", "whisper": "be_heard"}
ITEMS = {
    "boat": ("The Moon Boat", "a silver sail", 12, "The little boat waited for the moon."),
    "kite": ("The Red Kite", "a kite caught in a tree", 8, "The red kite tugged at its string."),
    "train": ("The Tiny Train", "a blue tunnel", 16, "The tiny train stopped beside the hill."),
}


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    title, picture, page, line = ITEMS[params.item]
    world.entities["book"] = Entity(id="book", label=title, location="reading_table",
                                    meters={"open_page": page, "bookmark_page": 0, "heard": 0})
    world.entities["chair"] = Entity(id="chair", label="the empty chair", location="reading_table",
                                     meters={"saved": 0})
    world.entities["sign"] = Entity(id="sign", label="the quiet-voices sign", location="wall",
                                    meters={"allows_soft_voices": 1})
    world.entities["hero"].beliefs.update(picture=picture, last_line=line)
    return world


def recover_page(world: World):
    friend, book = world.entities["friend"], world.entities["book"]
    _, picture, page, _ = ITEMS[world.params.item]
    if friend.beliefs.get("picture") != picture:
        raise StoryError("The friend needs the remembered picture before searching for the page.")
    book.meters.update(open_page=page, bookmark_page=page)


def fetch_book(world: World):
    hero, book = world.entities["hero"], world.entities["book"]
    if hero.beliefs.get("book_location") != book.location:
        raise StoryError("The reader has not learned where the book was put.")
    book.location = "reading_table"
    book.meters["reading_card"] = 1


def read_softly(world: World):
    hero, sign = world.entities["hero"], world.entities["sign"]
    if hero.beliefs.get("quiet") != "soft voices" or not sign.meters["allows_soft_voices"]:
        raise StoryError("The reader has not checked what quiet reading allows.")
    hero.meters["voice_volume"] = 1
    world.entities["book"].meters["heard"] = 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero, friend, book = (world.entities[key] for key in ("hero", "friend", "book"))
    h, f = hero.label, friend.label
    title, picture, page, line = ITEMS[params.item]
    world.narrate("beginning", f"{h} and {f} wanted to finish {title} before walking home. "
                  "Two small chairs waited beside the library's reading table.")

    if params.problem == "place":
        world.say("hero", "Will you save my place while I fill my water bottle?")
        world.say("friend", "Of course. Nobody else can have it.")
        book.meters["open_page"] = 0
        world.entities["chair"].meters["saved"] = 1
        friend.beliefs["saved_place"] = "the chair"
        world.narrate("closed_book", f"{h} went to the fountain. {f} closed the book and spread both arms across the empty chair.",
            question="Why did the readers lose their page?",
            cause=f"{h} asked for a place to be saved, but {f} understood that to mean the chair.",
            result=f"{f} closed the book without marking the page.")
        world.say("hero", "I'm back! Where were we?")
        world.say("friend", "Right here. I kept your chair.")
        if params.approach == "guess":
            hero.memes["frustration"] += 1
            world.say("hero", "You weren't listening. Now we've lost it.", tag="blurted")
            world.say("friend", "I was listening. I've been guarding this chair the whole time.")
            world.say("hero", "Oh. What did you think I wanted you to save?")
        else:
            world.say("hero", "Wait. What did you think I wanted you to save?")
        world.say("friend", "Your place to sit. The chair, not the page.", to="hero", reveal="saved_place")
        world.say("hero", "I meant the place in our story. I didn't say that bit.")
        world.say("friend", "I can help find it. What do you remember?")
        world.say("hero", f"There was {picture}. I wanted to see what happened next.", to="friend", reveal="picture")
        world.say("friend", f"Then let's look for {picture}, not guess a page number.")
        world.say("hero", "I'll turn slowly. You tell me when you see it.")
        recover_page(world)
        world.narrate("bookmark", f"The pages rustled. {f} tapped the right picture, and {h} slid a paper strip beside it.",
            question="How did they find and keep their reading place?",
            cause=f"{h} described {picture}, and {f} used that detail to find their reading place.",
            result="They put a paper bookmark at that page before reading on.")
        world.say("friend", "This is the one. The bookmark can guard it now.")
        world.say("hero", "Will you keep my place again? My chair this time.")
        world.say("friend", "Chair for me, page for the bookmark. That's a job I understand.")
        world.agree()
        world.narrate("ending", "The water bottle stood between the chairs. One paper corner peeked from the book, keeping a much smaller place.",
            question="What did the friends learn to say more clearly?",
            cause="The same word had meant a chair to one friend and a page to the other.",
            result="They named the chair and the page separately when asking for help.")

    elif params.problem == "return":
        world.say("hero", "Have you finished looking at the picture? Put it back when you're done.")
        world.say("friend", "All right. Then I'll choose our next book.")
        book.location = "return_trolley"
        friend.beliefs["book_location"] = "return_trolley"
        world.narrate("moved_book", f"{f} set {title} on the return trolley by the door. "
                      f"When {h} reached for it, the reading table was empty.",
            question="Why was the book missing from the reading table?",
            cause=f"{f} thought 'put it back' meant putting the book on the return trolley.",
            result=f"{h} had meant the reading table, so the two friends expected different places.")
        world.say("hero", "But we haven't finished the story.")
        world.say("friend", "I only finished looking at the picture.")
        if params.approach == "guess":
            hero.memes["frustration"] += 1
            world.say("hero", "Someone must have taken it. I'll check its shelf.")
            world.narrate("wrong_search", f"{h} hurried to the shelf. The book was not between the bookends.")
            world.say("friend", "I don't think another reader has it. You haven't asked where I put it.")
            world.say("hero", "You're right. Where is it?")
        else:
            world.say("hero", "Before I go hunting, where did you put it?")
        world.say("friend", "On the return trolley by the door.", to="hero", reveal="book_location")
        world.say("hero", "Oh! I meant back on this table.")
        world.say("friend", "Then I did a very good job of the wrong job.")
        world.say("hero", "I gave you half a direction. Can we go and get it?")
        world.say("friend", "Yes. Look for the cover, right beside the trolley handle.")
        fetch_book(world)
        world.narrate("fetch", f"They walked to the trolley together. {h} carried the book back; "
                      f"{f} wrote READING on a small card and set it on their table.",
            question="How did the friends recover the book?",
            cause=f"{f} told {h} that the book was on the return trolley.",
            result="They fetched it together and put it on the table beside a READING card.")
        world.say("hero", "That card tells us this book isn't finished yet.")
        world.say("friend", "What shall I do when we really are finished?")
        world.say("hero", "Put it on the return trolley. Not just 'back somewhere.'")
        world.say("friend", "Good. Somewhere is a very big place.")
        world.say("hero", "And our story is still right here.")
        world.agree()
        world.narrate("ending", f"{f} pushed the two chairs closer. {title} lay open between them, with the little READING card beside its cover.",
            question="How did they make the new instruction clearer?",
            cause="The word 'back' had not named a particular place.",
            result="They agreed to name the return trolley when they meant to finish with a book.")

    else:
        hero.beliefs["quiet"] = "no voice at all"
        friend.beliefs["quiet"] = "soft voices"
        hero.meters["voice_volume"] = 0
        world.say("friend", "Your lips are moving, but I can't hear the story.")
        world.say("hero", "I'm reading quietly. See the sign?")
        world.say("friend", "I see it. I still want to hear what the boat does." if params.item == "boat"
                  else "I see it. I still want to hear what happens next.")
        world.narrate("unheard", f"{h} pointed at QUIET VOICES on the wall. The next line stayed inside {h}'s head.",
            question="Why could one friend not follow the story?",
            cause=f"{h} thought quiet reading meant making no sound at all.",
            result=f"{f} could see the moving lips but could not hear the words.")
        if params.approach == "guess":
            hero.memes["frustration"] += 1
            world.say("hero", "Perhaps you should move closer.")
            world.narrate("closer", f"{f} moved the chair until their elbows nearly touched.")
            world.say("friend", "I'm as close as a bookmark now. I still can't hear silence.")
            world.say("hero", "Then moving your chair wasn't the answer.")
        else:
            world.say("hero", "Am I too far away, or am I not making any sound?")
            world.say("friend", "There isn't any sound to hear, even from here.")
        world.say("hero", "Does quiet have to mean no voice at all?")
        world.say("friend", "The sign says quiet voices. A soft voice is still a voice.", to="hero", reveal="quiet")
        world.say("hero", "So I can read to you without reading to the whole library?")
        world.say("friend", "Exactly. Try one line. I'll tell you if I can hear.")
        read_softly(world)
        world.say("hero", line, tag="whispered")
        world.say("friend", "I heard every word. That's our story coming back.")
        world.narrate("whisper", f"The words reached {f} without making the reader at the next table look up.",
            question="What change let both friends enjoy the story?",
            cause=f"{f} explained that the sign allowed a soft voice, rather than requiring silence.",
            result=f"{h} read one line softly, and {f} could hear it.")
        world.say("hero", "Your turn. I'll be the listening one.")
        world.say("friend", "Tell me if my voice gets too big.")
        world.say("hero", "I will. A little voice has room for both of us.")
        world.agree()
        world.narrate("ending", f"{f} bent over the next line. The two chairs stayed close, and a small shared voice followed a finger across the page.",
            question="How did they check that their solution worked?",
            cause=f"{h} tried reading one line in a soft voice.",
            result=f"{f} confirmed that every word could be heard before they continued.")
    sample = world.sample()
    check_sample(sample)
    return sample


def check_ending(world: World):
    book = world.entities["book"]
    problem = world.params.problem
    _, _, page, _ = ITEMS[world.params.item]
    if problem == "place" and (book.meters["bookmark_page"] != page or book.meters["open_page"] != page):
        raise StoryError("The page must be found and actually bookmarked.")
    if problem == "return" and (book.location != "reading_table" or not book.meters.get("reading_card")):
        raise StoryError("The book must be fetched, not merely promised.")
    if problem == "quiet" and not book.meters["heard"]:
        raise StoryError("The listener must hear a spoken line.")

ASP_RULES = """
valid(P,S) :- problem(P,N), solution(S,N).
#show valid/2.
"""


def valid_combos() -> list[tuple[str, str]]:
    return [(problem, solution) for problem, need in PROBLEMS.items()
            for solution, capability in SOLUTIONS.items() if need == capability]


def asp_facts() -> str:
    from asp import fact
    return "\n".join([fact("problem", key, value) for key, value in PROBLEMS.items()]
                     + [fact("solution", key, value) for key, value in SOLUTIONS.items()])


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def validate_params(params: StoryParams):
    if (params.problem, params.solution) not in valid_combos():
        raise StoryError(f"{params.solution!r} cannot solve {params.problem!r}; choose a compatible action.")
    if params.approach not in APPROACHES or params.item not in ITEMS:
        raise StoryError("Unknown approach or story item.")
    if params.hero == params.friend:
        raise StoryError("The two speakers must have different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.hero, params.friend)):
        raise StoryError("Use simple capitalized names, such as Mia and Ben.")


def check_sample(sample: StorySample):
    world = sample.world
    check_ending(world)
    turns = [event for event in world.history if event.kind == "speech"]
    if len(turns) < 14 or any(sum(event.speaker == key for event in turns) < 5 for key in ("hero", "friend")):
        raise StoryError("Both characters need sustained speaking turns.")
    if not any(event.revealed for event in turns):
        raise StoryError("The conversation must pass on useful information.")
    if len(sample.story_qa) < 3 or any(not event.cause or not event.result for event in world.history if event.question):
        raise StoryError("Grounded QA needs causes and consequences.")
    if any(world.entities[key].memes["trust"] < 1 for key in ("hero", "friend")):
        raise StoryError("The final agreement has not happened.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--approach", choices=APPROACHES)
    parser.add_argument("--item", choices=tuple(ITEMS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    candidates = [(p, s) for p, s in valid_combos()
                  if (args.problem is None or p == args.problem)
                  and (args.solution is None or s == args.solution)]
    if not candidates:
        raise StoryError("That solution does not address the selected problem.")
    problem, solution = rng.choice(candidates)
    hero = args.hero or rng.choice([name for name in NAMES if name != args.friend])
    friend = args.friend or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(hero=hero, friend=friend, problem=problem, solution=solution,
                         approach=args.approach or rng.choice(APPROACHES),
                         item=args.item or rng.choice(tuple(ITEMS)), seed=args.seed)
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree on compatible problem/solution pairs.")
    tested = 0
    for problem, solution in valid_combos():
        for approach in APPROACHES:
            for item in ITEMS:
                sample = generate(StoryParams(problem=problem, solution=solution,
                                               approach=approach, item=item))
                check_sample(sample)
                tested += 1
    print(f"OK: {tested} story states; {len(valid_combos())} Python/ASP-compatible pairs.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for pair in sample.story_qa:
            print(f"\nQ: {pair.question}\nA: {pair.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps(dict(entities=sample.world.snapshot(),
                              history=[asdict(event) for event in sample.world.history]), indent=2))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_combos())))
            return 0
        rng = random.Random(args.seed)
        if args.all:
            choices = [(p, s, a) for p, s in valid_combos() for a in APPROACHES
                       if (args.problem is None or p == args.problem)
                       and (args.solution is None or s == args.solution)
                       and (args.approach is None or a == args.approach)]
            if not choices:
                raise StoryError("No compatible combinations match these options.")
            params_list = []
            for problem, solution, approach in choices:
                fields = vars(args) | dict(problem=problem, solution=solution, approach=approach)
                params_list.append(resolve_params(argparse.Namespace(**fields), rng))
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]
        samples = [generate(params) for params in params_list]
        if args.json:
            payloads = [sample.to_dict() for sample in samples]
            print(json.dumps(payloads[0] if len(payloads) == 1 else payloads, ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
