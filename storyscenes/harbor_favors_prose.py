"""Realize reusable favor scenes from enacted replies, work and returns."""
from .capabilities.reading import Document, Statement
from .harbor_favors_story import ACTORS, NEED


WANTS = {"boat": "float the little boat", "flags": "unpack the paper flags", "chart": "read the faint directions on the chart"}
SPOKEN_WANTS = {"boat": "float my little boat", "flags": "unpack my paper flags", "chart": "read the faint directions on my chart"}
SHORT = {"boat": "the boat", "flags": "the flags", "chart": "the chart"}
TOOLS = {"rope": "rope", "scissors": "scissors", "lantern": "lantern"}


def render(spec, state):
    names = {a: state.get("entities", a).name for a in ACTORS}
    kinds = {a: state.get("favor_projects", a).kind for a in ACTORS}
    root = kinds["ari"]
    rows, completed, returned = [], set(), []
    inquiries = state.tables["favor_inquiries"]
    event_by_action = {e.action.id: e.id for e in state.events}
    positions = {e.id: i for i, e in enumerate(state.events)}

    def add(id, text, question, answer, events, focus="ari"):
        rows.append(Statement(id=id, text=text, question=question, answer=answer,
            kind=id, focus=focus, event_ids=tuple(events), entity_ids=tuple(ACTORS),
            needs=(rows[-1].id,) if rows else ()))

    opening = {
        "boat": 'Ari had a boat and a tub full of water, but the water was under a heavy hinged cover. A rope could pull it up. The little boat fitted comfortably in Ari\'s hands. It was a poor substitute for a harbor.',
        "flags": 'Ari\'s paper flags were meant to look like a procession. They were still inside a parcel closed with a sealed band. Ari could imagine them fluttering much more easily than Ari could open the parcel.',
        "chart": 'Ari had a harbor chart. Somewhere in its pale pencil marks was the direction to the landing. In the dim workshop, the marks looked like a very small person\'s very bad handwriting. Ari needed the lantern, not a more confident guess.',
    }[root]
    add("opening", opening, "What was Ari trying to do?",
        {"boat": "Ari wanted to float the little boat in the water tub. The heavy cover needed a rope before the boat could be lowered in.",
         "flags": "Ari wanted to unpack the paper flags. The sealed band around the parcel needed scissors.",
         "chart": "Ari wanted to read the directions to the landing. The faint pencil marks needed the lantern's light."}[root],
        ("initial/favor_projects/ari",))

    for event in state.events:
        op, actor = event.action.operation, event.action.actor
        name = names[actor]
        if op == "reply_favor_tool":
            inquiry = inquiries[event.action.args["inquiry"]]
            borrower, owner = names[inquiry.borrower], names[inquiry.owner]
            tool, kind = TOOLS[inquiry.tool], kinds[inquiry.owner]
            pronoun = "them" if inquiry.tool == "scissors" else "it"
            possessive = "their" if inquiry.tool == "scissors" else "its"
            earlier = any(r.borrower == inquiry.borrower and positions[r.asked_event] < positions[inquiry.asked_event]
                          for r in inquiries.values())
            question = f"Why did {owner} ask {borrower} to wait?" if inquiry.response == "wait" else f"How did {borrower} get the {tool}?"
            request = (f'"Could I have the {tool} now?" {borrower} asked.' if earlier else
                       f'"Could I borrow the {tool}?" {borrower} asked {owner}. "I want to {SPOKEN_WANTS[kinds[inquiry.borrower]]}."')
            support = [inquiry.asked_event, event.id]
            if inquiry.response == "wait":
                text = request + f'\n"After I {SPOKEN_WANTS[kind]}," {owner} said. "I want my own job finished first."\n{borrower} looked at {owner}. A short request had acquired another job.'
                answer = f"{owner} wanted to {WANTS[kind]} before lending the {tool}. This was a decision about going first, not a claim that the tool could not be lent."
            else:
                if inquiry.owner in completed:
                    reply = f'"Yes. Mine is finished," {owner} said. "Thank you for waiting."'
                elif (state.get("favor_policies", inquiry.owner).relaxed_event
                      and positions[state.get("favor_policies", inquiry.owner).relaxed_event] < positions[event.id]):
                    reply = f'"Yes. You go first," {owner} said. "Bring {pronoun} back when you are done."'
                else:
                    reply = f'"Take {pronoun}. My {SHORT[kind].removeprefix("the ")} can wait a little," {owner} said. "Bring {pronoun} back when you are done."'
                text = request + "\n" + reply + f'\n{borrower} agreed and took the {tool}. For once, the next step was small enough to fit in a hand.'
                support.append(event_by_action[f"borrow_{inquiry.borrower}"])
                answer = f"{owner} agreed to lend the {tool}, and {borrower} took {pronoun} after agreeing to the return terms. The loan did not make {borrower} {possessive} owner."
            add(event.id, text, question, answer, support, inquiry.borrower)
        elif op == "relax_favor_priority":
            cycle = list(event.data["cycle"])
            others = [names[a] for a in cycle if a != actor]
            look = "looked at " + others[0] if len(others) == 1 else "looked from " + " to ".join(others)
            text = f'{name} {look}. "We all keep saying after me."\nNo one had put a tool into another hand.\n"All right," {name} said. "I do not have to be first. Somebody else can start."'
            add(event.id, text, f"What did {name} change after hearing the requests?",
                f"{name} dropped the demand to finish first after the requests formed a waiting cycle. This allowed a loan before {name}'s own project was complete.",
                (event.id, *event.causes), actor)
        elif op == "complete_favor_work":
            kind = kinds[actor]
            text = {
                "boat": f'{name} looped the rope round the handle of {name}\'s covered tub and pulled. The heavy lid swung up and stayed on its hinge. Then {name} lowered the little boat onto the water and let go. It moved a little farther than the hands that had held it. "There," {name} said. "Now it is a boat."',
                "flags": f'{name} slid the scissors under the sealed band on {name}\'s parcel and cut it. Inside lay the folded paper flags, every little point still whole. {name} paused over them. "There is the beginning of my procession."',
                "chart": f'{name} held the lantern over {name}\'s chart. The pale marks joined into words: "Past the red buoy." There had been a direction there all along. {name} read it again, more slowly. A small pool of light had made the harbor a little less large.',
            }[kind]
            if any(kinds[a] == kind for a in completed):
                text = {
                    "boat": f'Now {name} used the rope to lift the cover of a different tub: {name}\'s own. The little boat went onto its water. "Room for mine, too," {name} said, letting go.',
                    "flags": f'{name}\'s own parcel was next. It held {name}\'s own flags. One cut opened the sealed band, leaving the flags whole. "My turn," {name} said. It sounded better now that it was true.',
                    "chart": f'With the same lantern, {name} read a different sheet: {name}\'s own chart. Its faint directions also said "Past the red buoy." The light had not been used up by helping someone else.',
                }[kind]
            answer = {
                "boat": f"{name} used the rope to raise the tub cover, then lowered the boat onto the water. The boat floated without being held.",
                "flags": f"{name} used the scissors to cut the sealed band and open the parcel. The paper flags inside remained whole.",
                "chart": f"{name} used the lantern to read the chart's faint directions. The directions said to go past the red buoy.",
            }[kind]
            support = [event.id, event_by_action[f"use_{actor}"]]
            if kind == "boat":
                support.append(event_by_action[f"open_{actor}"])
            add(event.id, text, f"What did {name} actually accomplish?", answer, support, actor)
            completed.add(actor)
        elif op == "complete_return":
            loan = state.get("loans", event.data["loan_id"])
            terms = state.get("loan_terms", loan.terms)
            owner, tool = names[terms.owner], TOOLS[terms.object]
            pronoun, possessive, was = ("them", "their", "were") if terms.object == "scissors" else ("it", "its", "was")
            text = f'{name} offered the {tool} back, and {owner} took {pronoun}. "That part was easy," {name} said.\n"It matters," {owner} answered. The {tool} {was} back with {possessive} owner, not merely lying somewhere nearby.'
            add(event.id, text, f"Was {name}'s loan settled?",
                f"Yes. {name} returned the {tool} directly to {owner}, who accepted {pronoun}. {name} no longer had that borrowed tool to return.",
                (event.id,), actor)
            returned.append(terms.object)

    done = state.get("favor_session", "end").completed
    if done:
        image = {"boat": "Ari's boat rested on the water, with no hands underneath it.",
                 "flags": "Ari's paper flags lay in their open parcel, ready to be unfolded.",
                 "chart": "On Ari's chart, the route still ran past the red buoy. Ari could now name the way."}[root]
        if any(p.relaxed_event for p in state.tables["favor_policies"].values()):
            tail = "The tools had gone back. The order of things had not: someone had let another person go first."
        elif len(completed) > 1:
            tail = "Ari's job had turned out to have other people's jobs inside it. They were not inside it any more."
        elif returned:
            tail = "Ari looked at the borrowed tool, back in its owner's hand. Asking had taken a moment. Someone else had made room for the answer."
        else:
            tail = "For this job, Ari had already had the right tool. No borrowed tools needed to be returned."
        answer = f"Ari had managed to {WANTS[root]}. Every tool borrowed during the story had been returned to its owner."
    else:
        image = {"boat": "Ari's little boat was still in Ari's hands. The water stayed under its cover.",
                 "flags": "Ari's flags were still sealed in their parcel. Imagining them fluttering had not opened it.",
                 "chart": "The faint marks were still on Ari's chart, and Ari still could not read them."}[root]
        tail = '"We have all kept our tools," Ari said. It sounded like a success until Ari looked at the unfinished work.'
        answer = f"Ari had not managed to {WANTS[root]}. The requests ended in a waiting cycle, with everyone in that cycle still insisting on going first."
    add("ending", image + " " + tail, "What had changed for Ari by the end?", answer,
        (state.get("favor_session", "end").event_id,))
    return Document(title=spec.title, statements=tuple(rows))
