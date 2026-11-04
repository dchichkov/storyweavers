"""Second-pass authored scenes, social practices, consequences, and endings."""
from dataclasses import replace
from engine import Beat, Exchange, Goal, Performance


def P(id, *lines, effects=(), when=()):
    return Performance(id, tuple(lines), tuple(effects), tuple(when))


def G(id, *variants):
    return Goal(id, tuple(variants))


def C(path, op, value):
    return (path, op, value)


def E(op, path, value):
    return (op, path, value)


def public_fact(fact):
    return tuple(E("set", "people." + p + ".knows." + fact, True) for p in ("mara", "eli", "player"))


TOPICS = (
    Beat("soup", "topics", "dinner", 3, (
        G("entry", P("soup", 'From the kitchen comes the quiet click of the oven cooling. Eli has switched it off without bringing the food through.',
                     'Mara: "You made the soup."', 'Eli: "Your mother\'s recipe."',
                     effects=(E("set", "props.soup.state", "cooling"),))),
        G("memory", P("recipe", 'Mara: "She never measured the cumin. You wrote down half a teaspoon and she laughed at you."',
                      'Eli: "I wanted to get it right."', 'Mara: "I know you did."',
                      effects=(E("add", "people.mara.memes.anger", -1),))),
        G("turn", P("care", 'Eli: "I can still do that. Make something you like."',
                    'Mara: "Yes. But you have to let me tell you when I like something else."',
                    'He removes the serving spoon from its wrapping and lays it between them.')),
    ), resume='Eli looks toward the kitchen. "The soup can wait another minute."'),
    Beat("blue_mug", "topics", "home", 3, (
        G("entry", P("chip", 'Eli brings water in a blue mug with a chip under the handle. Mara gives him a look.',
                     'Eli: "I know. We have glasses."', 'Mara: "You gave our guest the best mug."',
                     effects=(E("set", "props.mug.location", "table"), E("set", "props.mug.state", "filled")))),
        G("history", P("bus", 'Mara: "We bought that at a service station when the van broke down. Our entire kitchen was in the van."',
                       'Eli: "You said if we owned a mug we technically had a home."',
                       'They laugh at the same time, then stop as if they have been caught.')),
        G("turn", P("home", 'Mara runs a finger around the chip. "It was enough because neither of us pretended it was permanent."',
                    'Eli: "I think I have been trying to make everything unbreakable."',
                    'He leaves the damaged mug on the table, where it is still useful.',
                    effects=(E("set", "people.eli.insight", True), E("add", "people.eli.memes.fear", -1)))),
    ), resume='Mara turns the blue mug by its handle. "I was remembering the van."'),
    Beat("wrapped_canvases", "topics", "family", 4, (
        G("entry", P("wrapped", 'You ask about the small painting above the radiator. Mara says her mother painted it before Mara was born.',
                     'Eli: "She had more talent than she knew."', 'Mara: "She knew. That was the worst of it."')),
        G("history", P("canvases", 'Mara: "We found twenty-three blank canvases in the spare room after she died. She had been buying one every birthday."',
                       'Eli looks up at the painting. "You never told me that."',
                       'Mara: "I couldn\'t make it a story with a good ending."',
                       effects=public_fact("mara_fear") + (E("set", "people.mara.heard", True),))),
        G("turn", P("not_mother", 'Eli: "I don\'t want that for you."',
                    'Mara: "Then sometimes you will have to want things for me that put me somewhere else."',
                    'Eli starts to answer and closes his mouth. It is a small, deliberate effort.',
                    effects=(E("add", "people.mara.trust_partner", 1),))),
    ), resume='Mara looks at the painting above the radiator. "About my mother—"'),
    Beat("useful_hands", "topics", "work", 4, (
        G("entry", P("scar", 'Eli notices you looking at the white scar on his thumb. "That was her bicycle. The first time I fixed it."',
                     'Mara: "You refused money."', 'Eli: "You bought me dinner."')),
        G("history", P("needed", 'Mara: "I would have bought you dinner if you had made the bike worse."',
                       'Eli: "I didn\'t know that."', 'Mara: "You were funny. I liked you. The bike was a bike."',
                       effects=public_fact("eli_fear") + (E("set", "people.eli.heard", True),))),
        G("turn", P("not_needed", 'Eli rests his hands flat on the table. "I think I am better at being needed than being wanted."',
                    'Mara: "Being wanted involves letting me choose."',
                    'He turns his hands palm up, as if he has finally put down a tool.',
                    effects=(E("set", "people.eli.insight", True), E("add", "people.eli.memes.fear", -1)))),
    ), resume='Eli looks at the scar on his thumb. "I keep trying to fix things."'),
    Beat("lost_hours", "topics", "work", 5, (
        G("entry", P("hours", 'Mara: "You have been home on Thursdays. I thought the new hours were good."',
                     'Eli: "They are not new hours. They are fewer hours."')),
        G("truth", P("admit", 'Eli: "The firm cut my time in June. I said freelance because it sounded chosen. I have had two freelance jobs in four months."',
                     'Mara: "You could have told me."', 'Eli: "I wanted to tell you after I had already made it all right."',
                     effects=public_fact("eli_need") + (E("set", "people.eli.heard", True),))),
        G("turn", P("solution", 'Mara: "You don\'t have to present your life to me with the broken parts edited out."',
                    'Eli: "I thought you were tired of the broken parts."',
                    'Mara moves the water toward him. "I am tired of finding them by accident."',
                    effects=(E("add", "people.eli.trust_partner", 1),))),
    ), when=(C("people.eli.trust_player", "ge", 3),), resume='Eli: "There is more to say about my hours."'),
    Beat("test_piece", "topics", "art", 4, (
        G("entry", P("eye", 'Mara describes a painting she restored in the evenings: a woman whose eyes had disappeared under old varnish.',
                     'Eli: "That was what you were doing at the desk?"', 'Mara: "I thought you weren\'t interested."')),
        G("history", P("judgment", 'Mara: "I cleared one eye. The expression changed the whole picture. The director wrote to ask why I had stopped there."',
                       '"I told him the other eye needed a different solvent. He said that was the answer he had hoped for. Not speed. Judgment."',
                       effects=public_fact("mara_need") + (E("set", "people.mara.heard", True),))),
        G("turn", P("interest", 'Eli: "Would you show me a photograph of it? Not now. When you want to."',
                    'Mara looks surprised. "Yes. I would."',
                    'For a moment, the person she becomes away from home is someone he might be allowed to meet.',
                    effects=(E("add", "people.mara.trust_partner", 1),))),
    ), resume='Mara: "I was telling you about the painting, not the argument."'),
    Beat("refund_window", "topics", "money", 5, (
        G("entry", P("number", 'Mara asks for the receipt. Eli slides it across without covering the amount.',
                     'Mara: "Eight hundred pounds."', 'Eli: "Yes."')),
        G("terms", P("deadline", 'Eli: "There is a cooling-off period. If I call before noon tomorrow, we can recover six hundred. Two hundred is an administration fee."',
                     'Mara: "That is not nothing. It is also not everything."',
                     effects=public_fact("refund"))),
        G("turn", P("choice", 'Eli: "I keep thinking if we go ahead, none of it has been wasted."',
                    'Mara: "Spending more to prove the first money wasn\'t a mistake is still a choice."',
                    'Eli reads the deadline again. This time he underlines it.',
                    effects=(E("set", "props.receipt.state", "annotated"),))),
    ), when=(C("people.eli.disclosed", "eq", True),), resume='Eli reads the receipt again. "About the deadline—"'),
    Beat("monday_train", "topics", "time", 5, (
        G("entry", P("train", 'Eli: "Monday morning or Monday night?"', 'Mara: "The nine-twelve. They want us there for lunch."',
                     'Eli nods as if the timetable is a set of instructions he can follow.')),
        G("weeks", P("schedule", 'Mara: "There is a break after the first six weeks. I could come back then. After that we would have to plan."',
                     'Eli: "You already looked at that."', 'Mara: "Yes. Leaving was never the same thing as disappearing."',
                     effects=public_fact("schedule"))),
        G("turn", P("calendar", 'Eli brings the kitchen calendar to the table, then stops before opening it.',
                    'Eli: "Would you like to write it, or shall I?"', 'Mara: "Let me."',
                    effects=(E("set", "props.calendar.location", "table"),))),
    ), when=(C("people.mara.disclosed", "eq", True),), resume='Mara touches the calendar. "The train is only part of the plan."'),
    Beat("father_call", "topics", "family", 5, (
        G("entry", P("ring", 'Eli\'s phone lights up: DAD. He turns it face down.',
                     'Mara: "You can answer."', 'Eli: "He will want to know if you liked the surprise."',
                     effects=(E("set", "props.phone.state", "missed_call"),))),
        G("pressure", P("told", 'Mara: "How many people knew before me?"',
                       'Eli: "He lent me the ladder to look at the ceiling. I made it sound like we had agreed."',
                       'Mara: "So tomorrow, if I say no, I am taking something away from you in front of him."')),
        G("turn", P("boundary", 'Eli picks up the phone, then puts it back down without dialing.',
                    'Eli: "I will tell him I got ahead of myself. You don\'t have to be the person who spoiled it."',
                    'Mara: "I would like to hear you say that when I am not in the room."',
                    effects=(E("set", "people.eli.insight", True),))),
    ), when=(C("people.eli.disclosed", "eq", True),), resume='Eli glances at the dark phone. "I should have talked to you before my father."'),
    Beat("guest_as_witness", "topics", "dinner", 5, (
        G("entry", P("invitation", 'Mara asks who sent the invitation. Eli says he did.',
                     'Mara: "You said we had both been meaning to."', 'Eli: "We had. Once."')),
        G("admit", P("witness", 'Eli: "I thought with someone else here, we would finish a conversation instead of leaving it on the stairs."',
                     'Mara: "You invited a referee and told them to bring wine."',
                     'Eli: "I invited someone who remembers us being kind."')),
        G("turn", P("job", 'Mara looks at you. "You can be our friend. You don\'t have to be evidence that one of us is right."',
                    'Eli: "That is fair." He moves your chair back from the space between theirs.',
                    effects=(E("set", "people.player.witness_named", True),))),
    ), resume='Mara: "We were talking about why we asked you here."'),
)


AFTERMATH = (
    Beat("two_columns", "aftermath", "money", 3, (
        G("entry", P("paper", 'Eli finds a pencil and turns a spare envelope over. He draws two columns, then crosses out the line between them.',
                     'Mara: "What was that?"', 'Eli: "Mine and yours. We should start with what we actually have."')),
        G("cost", P("figures", 'They write down the deposit, the recoverable amount, the train fare, and the rent.',
                    'Mara: "The two hundred pounds is real. We can be angry about it and still know what happens next."',
                    'Eli writes the call deadline at the top, larger than the amounts.',
                    effects=(E("set", "props.budget.state", "written"),))),
        G("turn", P("not_receipt", 'Eli: "I will make the call. I won\'t tell the agent that you changed your mind."',
                    'Mara: "Thank you. I hadn\'t changed a mind I wasn\'t asked for."',
                    'He leaves the pencil between their hands instead of keeping it.',
                    effects=(E("set", "people.eli.accountable", True),))),
    ), priority=2, when=(C("people.eli.commitment", "eq", True),), resume='Eli turns the envelope around. "We were making the numbers visible."'),
    Beat("calendar_margin", "aftermath", "time", 3, (
        G("entry", P("dates", 'Mara opens the calendar to Monday. She writes the train time in the margin, leaving the day itself mostly empty.',
                     'Eli: "You don\'t have to fill every square to make me feel better."')),
        G("distance", P("six_weeks", 'Mara marks the break after six weeks. "This is a visit, not a test I have to pass."',
                        'Eli: "And if one of us finds the distance harder than we expected, we say so before making another plan around it."',
                        'Mara draws a small question mark after the visit rather than an exclamation point.',
                        effects=(E("set", "props.calendar.state", "agreed_dates"),))),
        G("turn", P("room", 'Mara: "I should have let you into the planning. That doesn\'t mean asking permission to want it."',
                    'Eli: "I am learning the difference."',
                    'The open calendar takes up the place where your plate was supposed to go.',
                    effects=(E("set", "people.mara.accountable", True),))),
    ), priority=2, when=(C("people.mara.commitment", "eq", True),), resume='Mara keeps a finger on Monday. "We do not have to plan all six months tonight."'),
    Beat("sister_spare_room", "aftermath", "space", 3, (
        G("entry", P("message", 'Mara sends her sister a message asking whether the spare room is free. She writes "one night" and does not erase it.',
                     'Eli watches the tabletop instead of the screen.', effects=(E("set", "props.phone.state", "room_requested"),))),
        G("reply", P("yes", 'The answer comes back: Of course. Mara reads those two words aloud.',
                     'Eli: "Do you need the bigger bag?"', 'Mara: "The small one. Please don\'t make it mean more than I said."',
                     effects=(E("set", "props.bag.state", "chosen"),))),
        G("turn", P("key", 'Eli: "Keep your key."', 'Mara: "I was going to."',
                    'He nods. The exchange is awkward, but neither turns it into a threat.')),
    ), priority=3, when=(C("people.player.requested_space", "eq", True),), resume='Mara checks her phone. "My sister has a room."'),
    Beat("damaged_confidence", "aftermath", "privacy", 5, (
        G("entry", P("mara", 'Mara: "Before we talk about our promises to each other, I need to talk about yours to me."',
                     'She looks at you, not at Eli.', when=(C("people.mara.privacy_breached", "eq", True),)),
          P("eli", 'Eli: "You made the thing I was afraid to say into a thing I couldn\'t choose to say."', 'He looks at you, not at Mara.')),
        G("witness", P("no_prize", 'The other host does not come to your defense. Learning the truth has not made them grateful for the way it arrived.',
                       'Mara: "We still have to deal with what we did. You don\'t get to use that to make your part disappear."')),
        G("turn", P("boundary", 'Eli moves your glass a little closer to your side of the table.',
                    'Eli: "If there is another conversation after tonight, it won\'t happen with someone carrying messages between us."',
                    'No one asks you to answer.')),
    ), priority=4, when=(C("people.player.betrayal", "eq", True),), resume='Mara: "We have not finished talking about what happened in the kitchen."'),
    Beat("unlearning_gifts", "aftermath", "care", 3, (
        G("entry", P("gift", 'Eli: "I keep wanting to do something useful before you leave. Something bigger than words."',
                     'Mara: "Ask me for something small."')),
        G("answer", P("box", 'Eli: "Do you want help packing?"', 'Mara: "With the brushes. There are rules about how the tips are wrapped."',
                      'Eli: "Then you can teach me the rules."')),
        G("turn", P("small", 'Mara brings an empty brush roll to the table. She shows him where a sleeve must stay loose.',
                    'For once he waits until she has finished explaining before reaching for it.',
                    effects=(E("set", "props.brush_roll.location", "table"), E("set", "props.brush_roll.state", "demonstrated")))),
    ), priority=1, when=(C("people.mara.disclosed", "eq", True), C("people.eli.accountable", "eq", True),
                        C("people.player.requested_space", "eq", False), C("people.player.betrayal", "eq", False)),
         resume='Mara holds the brush roll open. "It helps if the bristles have room."'),
    Beat("cold_dinner", "aftermath", "dinner", 2, (
        G("entry", P("cold", 'Eli goes to fetch the soup. When he returns, the serving dish is only warm against his hands.',
                     'Eli: "I can heat it again."', 'Mara: "It doesn\'t have to be an occasion. We can just eat."',
                     effects=(E("set", "props.soup.location", "table"), E("set", "props.soup.state", "served")))),
        G("ordinary", P("meal", 'They each take a little. You do too. For a minute the sounds are ordinary: a spoon, the water jug, a chair against the floor.',
                       'No one proposes a toast.', effects=(E("set", "props.plates.state", "used"),))),
        G("turn", P("still_here", 'Mara: "We are still here."', 'Eli: "For tonight."',
                    'She nods. It is the first answer this evening neither of them tries to enlarge.')),
    ), weight=0.5, resume='Eli gestures to the serving dish. "Please. Have some while there is still warmth in it."'),
    Beat("separate_futures", "aftermath", "future", 4, (
        G("entry", P("plain", 'Mara: "I don\'t want us to call this a temporary arrangement just because the other word sounds like failure."',
                     'Eli: "Then we do not have to call it that."')),
        G("belongings", P("practical", 'They begin with the ordinary things: the tenancy, the standing orders, which boxes can wait until after Monday.',
                       'Eli: "The photograph is yours if you want it."', 'Mara: "I want us both to have been happy in it. Can we leave it there for now?"')),
        G("turn", P("choice", 'They leave the photograph on the sideboard. Neither turns it over.',
                    'The past can remain true without being an instruction for what happens next.')),
    ), priority=3, when=(C("people.player.requested_separation", "eq", True),), resume='Mara: "We can decide the practical things without making the past ugly."'),
)


CRISES = (
    Beat("privacy_crisis", "crisis", "privacy", 7, (
        G("collision", P("cost", 'Eli: "We invited you into our home. One of us tried to trust you with something difficult."',
                         'Mara: "And now the kitchen feels like another room where you have to prepare a defense."')),
        G("own_part", P("still_ours", 'Mara: "We do not get to make this all about our guest. We were keeping things from each other before the doorbell rang."',
                        'Eli: "I know. But I would like the next thing I hear to come from you."')),
        G("boundary", P("no_messenger", 'They turn their chairs a fraction away from you and toward each other.',
                        'You can remain a witness. You have lost the right to be their interpreter.')),
    ), priority=5, when=(C("people.player.betrayal", "eq", True),), resume='Eli: "We need to speak to each other directly now."'),
    Beat("no_more_referee", "crisis", "future", 6, (
        G("choice", P("judge", 'Eli starts to ask you what you think. Mara stops him with a hand on the table.',
                      'Mara: "We cannot keep making our friend responsible for the next sentence."')),
        G("question", P("both_known", 'Mara: "I want the residency. You want the workshop. We have told each other what we decided. We still have not asked what we need."',
                        'Eli: "All right. Ask me."',
                        when=(C("people.mara.disclosed", "eq", True), C("people.eli.disclosed", "eq", True))),
          P("still_hidden", 'Mara: "We have told each other pieces. We have not told each other enough to make a decision."',
            'Eli looks at the papers on the sideboard. "No. We haven\'t."')),
        G("opening", P("floor", 'They look at each other for several seconds. If you leave this silence alone, something might finally fit inside it.',
                        effects=(E("set", "people.player.opened_floor", True),))),
    ), priority=1, when=(C("people.player.witness_named", "eq", True),), resume='Mara: "We were trying to stop asking you to decide for us."'),
)


MIXINS = {
    "family": (
        (P("painting", 'Mara follows your glance toward the painting above the radiator. "My mother did that one. Before she had children."',
           'Eli: "Mara inherited her eye."', 'Mara: "I am trying not to inherit all her postponements."'),),
        (P("canvases", 'Mara: "After she died, we found the canvases she had bought for herself. Twenty-three of them. Every one blank."',
           'Eli looks at the painting for a long time. "I wish you had told me what you saw when you looked at it."',
           effects=public_fact("mara_fear") + (E("set", "people.mara.heard", True),)),),
        (P("difference", 'Mara: "You are not my father. I know that. Sometimes I make you answer for things he did."',
           'Eli: "Then let me be the person in front of you. Even if I get it wrong."',
           effects=(E("set", "people.mara.insight", True), E("add", "people.mara.memes.fear", -1))),),
    ),
    "work": (
        (P("useful", 'Eli: "I mend things. Doors, bikes, whatever people bring. Mara works on things you can ruin by trying too hard to fix them."',
           'Mara: "That is a better description than you usually give."', 'He smiles briefly. "I do listen sometimes."'),),
        (P("short_hours", 'Eli: "There has been less work since June. I made the empty days sound like days I had chosen."',
           'Mara: "I thought you were enjoying being home."', 'Eli: "I wanted you to think that."',
           effects=public_fact("eli_need") + (E("set", "people.eli.heard", True),)),),
        (P("wanted", 'Eli: "When I can do something useful, I know what I am worth in the room."',
           'Mara: "I didn\'t fall in love with a repair service. I would like to see you when you aren\'t auditioning for the job."',
           effects=public_fact("eli_fear") + (E("set", "people.eli.insight", True),)),),
    ),
    "art": (
        (P("test", 'Mara: "I restored part of a portrait for a test. Just one eye. If you move too fast, what you think is dirt turns out to be somebody\'s shadow."',
           'Eli: "You never showed me."', 'Mara: "You never asked."'),),
        (P("judgment", 'Mara: "The director wanted to know why I stopped. He valued that I could tell where my certainty ended."',
           'Eli: "Is that what you wanted from me? Interest, without a solution?"', 'Mara: "That would have been a start."',
           effects=public_fact("mara_need") + (E("set", "people.mara.heard", True),)),),
        (P("look", 'Mara opens a photograph of the painting on her phone. Eli leans closer, then waits for her to point.',
           'She shows him where the varnish ends. He asks a question about the light.',
           'For a few sentences, she speaks to him in the voice she uses when she loves her work.',
           effects=(E("add", "people.mara.trust_partner", 1), E("set", "people.mara.insight", True))),),
    ),
    "money": (
        (P("public", 'Eli: "The deposit was eight hundred pounds. Saying the number out loud makes it sound less like an idea."',
           'Mara: "It was never just an idea to our bank account."', when=(C("people.eli.disclosed", "eq", True),)),
         P("not_public", 'Mara: "We put money aside every month. It was meant to buy us choices."',
           'Eli looks toward the receipt. "I thought I was choosing one."')),
        (P("terms", 'Eli reads from the receipt. "Six hundred back if I call before noon tomorrow. Two hundred gone either way."',
           'Mara: "Then there is still something you can do without deciding my future for me."',
           effects=public_fact("refund"), when=(C("people.eli.disclosed", "eq", True),)),
         P("refused", 'Eli: "We should talk about the receipt before we start making promises about the money."')),
        (P("not_all", 'Mara: "I don\'t need the eight hundred pounds to become a reason I have to stay. I need to know what happens to the six hundred we can still recover."',
           'Eli: "One phone call. Before noon. I can do that."',
           effects=(E("set", "people.eli.insight", True),), when=(C("people.eli.disclosed", "eq", True),)),
         P("refused", 'Mara: "We still haven\'t said what the money was spent on."')),
    ),
    "time": (
        (P("monday", 'Mara: "The train is at nine-twelve on Monday. I have looked at the ticket so often I can see the numbers when I close my eyes."',
           'Eli: "There is a ticket too."', when=(C("people.mara.disclosed", "eq", True),)),
         P("time", 'Mara: "There is always a reason to wait for a better week. I am beginning to think the better week is a place people send things they don\'t want to face."')),
        (P("visit", 'Mara: "There is a break after six weeks. I could come home then. We could decide together how to handle the rest."',
           'Eli: "You imagined coming home."', 'Mara: "Of course I did."',
           effects=public_fact("schedule"), when=(C("people.mara.disclosed", "eq", True),)),
         P("refused", 'Mara: "You should ask me about the letter before we start discussing dates."')),
        (P("limit", 'Eli: "I can try six weeks without pretending I already know how six months will feel."',
           'Mara: "Then neither of us has to lie about being fine to protect a promise."',
           effects=(E("set", "people.mara.insight", True),), when=(C("people.mara.disclosed", "eq", True),)),
         P("refused", 'Mara rests a hand on the letter. "There are things I need to say first."')),
    ),
    "future": (
        (P("not_abstract", 'Eli: "I used to think the future meant more of this. A little less rent. Better chairs."',
           'Mara: "I think I need it to include something neither of us has seen yet."'),),
        (P("not_threat", 'Mara: "Being frightened of losing each other is not the same as wanting the same life."',
           'Eli: "And being angry tonight is not the same as never wanting it again."',
           'Neither asks you to settle that for them.'),),
        (P("permission_to_end", 'Mara: "If we stay together, I want it to be something we choose. Not a debt to all the years that came before."',
           'Eli: "I can hear that. Even if the choice is one I don\'t want."', effects=public_fact("future")),),
    ),
    "home": (
        (P("mug", 'Eli points to the chipped blue mug. "That was the first thing we owned together."',
           'Mara: "A service station. A broken van. Six pounds between us."'),),
        (P("small", 'Mara: "We bought one mug because we thought sharing it was romantic."',
           'Eli: "It was romantic until you made tea while I was brushing my teeth."',
           'Mara laughs. For a moment neither of them seems to be watching for a mistake.',
           effects=(E("add", "people.mara.memes.anger", -1), E("add", "people.eli.memes.anger", -1))),),
        (P("portable", 'Mara: "Home used to be a thing we made, not a place we had to keep proving we could not leave."',
           'Eli touches the mug\'s chipped handle. "I would like to remember how we did that."',
           effects=(E("set", "people.eli.insight", True), E("set", "people.mara.insight", True))),),
    ),
    "dinner": (
        (P("anniversary", 'Eli: "Eleven years. The actual day was Tuesday, but we wanted a whole evening."',
           'Mara: "We have certainly managed that."'),),
        (P("guest", 'Eli: "I asked you because you knew us before we became so careful with each other."',
           'Mara: "Or so careless. It depends which part you look at."', effects=(E("set", "people.player.witness_named", True),)),),
        (P("witness", 'Mara: "You don\'t have to carry an answer home with you."',
           'Eli: "But perhaps we could stop pretending there wasn\'t a question."', effects=(E("set", "people.player.opened_floor", True),)),),
    ),
}


def exit_effects(*effects):
    return (E("set", "people.player.location", "hallway"), E("set", "props.coat.location", "player"),
            E("set", "props.coat.state", "worn")) + tuple(effects)


ENDINGS = (
    ("broken_confidence", (P("excluded",
        'Mara: "We will finish this conversation ourselves." It is not a request for advice.',
        'Eli brings your coat. He does not make a joke about the evening going wrong.',
        'You leave them at the table. Through the closing door, you hear one of them ask the other a quiet question. This time you are not there to repeat the answer.',
        effects=exit_effects(E("set", "props.chairs.state", "guest_excluded"))),), (C("people.player.betrayal", "eq", True),)),
    ("separate", (P("chosen_separation",
        'Mara puts a blank envelope beside the calendar and writes her new address on it. Eli reads it and sets it where he will find it again.',
        'Eli: "I want to be someone you can tell things to, even if I am not the person you come home to."',
        'Mara: "I would like that. Not immediately. But I would."',
        'You collect your coat. The photograph stays upright on the sideboard. Beside it, the new address is in Mara\'s handwriting, not a secret someone else has uncovered.',
        effects=exit_effects(E("set", "props.address.state", "written"), E("set", "props.chairs.state", "apart"))),),
     (C("people.player.requested_separation", "eq", True),)),
    ("space", (P("night_apart",
        'Mara checks that her flat key is in her pocket, packs the small bag, and joins you in the hall.',
        'Eli: "Tomorrow?"', 'Mara: "Tomorrow. We do not have to decide what every tomorrow means tonight."',
        'He holds the door without standing in it. On the stairs she pauses to settle the bag on her shoulder. Her key rings softly against the buckle; she has not given it back.',
        effects=exit_effects(E("set", "people.mara.location", "hallway"), E("set", "props.bag.location", "mara"),
                             E("set", "props.bag.state", "packed"), E("set", "props.key.location", "mara_pocket"),
                             E("set", "props.key.state", "carried"))),), (C("people.player.requested_space", "eq", True),)),
    ("practical", (P("two_promises",
        'Eli writes "call before noon" on the envelope. Mara writes the time of the Monday train underneath and draws a line to the first six-week break.',
        'Eli: "I am still angry."', 'Mara: "So am I. We can do these things while we are angry."',
        'You leave them with the envelope between them. Nothing on it says that their relationship is fixed. It says who will make the call, when the train leaves, and when they will talk again.',
        effects=exit_effects(E("set", "props.budget.state", "commitments_written"), E("set", "props.calendar.state", "agreed_dates"))),),
     (C("people.mara.commitment", "eq", True), C("people.eli.commitment", "eq", True), C("people.player.requested_talk", "eq", False))),
    ("repair", (P("tomorrow",
        'Eli places the receipt beside the letter. He asks Mara whether she would like him to move his chair closer. She says yes.',
        'Mara: "Tomorrow I want to show you the painting. Then we can talk about the parts that frighten us."',
        'Eli: "I would like to see it." He does not offer to make a frame.',
        'You collect your coat. As the door closes, the two papers stay between their plates, uncovered. Their chairs are on the same side of the table, with room left between them.',
        effects=exit_effects(E("set", "props.letter.location", "table"), E("set", "props.receipt.location", "table"),
                             E("set", "props.chairs.state", "together"))),),
     (C("people.player.requested_talk", "eq", True), C("people.mara.accountable", "eq", True), C("people.eli.accountable", "eq", True),
      C("people.mara.trust_partner", "ge", 4), C("people.eli.trust_partner", "ge", 4),
      C("people.mara.memes.anger", "le", 5), C("people.eli.memes.anger", "le", 5))),
    ("unresolved", (
        P("truth", 'Mara: "We have said what happened. I do not know what to do with it yet."', 'Eli: "Neither do I."',
          'You take your coat. The papers remain in plain sight, but neither host moves their chair. The distance between the chairs has become something they can no longer pretend is only furniture.',
          effects=exit_effects(), when=(C("people.mara.disclosed", "eq", True), C("people.eli.disclosed", "eq", True))),
        P("mara_only", 'Mara waits for Eli to speak. He touches the face-down receipt and says good night instead.',
          'You collect your coat. The letter is no longer hidden. Beside it, the receipt is still a small white rectangle turned away from the room.',
          effects=exit_effects(), when=(C("people.mara.disclosed", "eq", True),)),
        P("eli_only", 'Eli waits for Mara to speak. She folds her letter along its existing crease and says good night instead.',
          'You collect your coat. The receipt lies in plain sight. The letter beside it has become smaller without becoming less important.',
          effects=exit_effects(), when=(C("people.eli.disclosed", "eq", True),)),
        P("polite", 'Eli: "We should do this again when things are less complicated."', 'Mara opens the door. "Good night."',
          'You take your coat. The letter stays folded and the receipt stays face down. Behind the courtesy, the two small papers continue to occupy the room.', effects=exit_effects()),
    ), ()),
    ("ejected", (P("door", 'Mara brings your coat. Eli opens the door and waits.',
        'Mara: "We can be unhappy with each other without giving you permission to be cruel to us."',
        'The door shuts behind you. The conversation on the other side starts again, lower now. You have become the one subject on which they agree.', effects=exit_effects()),), ()),
    ("left", (P("departure", 'You say that you should go and collect your coat from the hall hook.',
        'Neither asks you to stay. Eli walks you to the door; Mara remains by the table.',
        'From the hallway you can still see the third chair. When Eli closes the door, it disappears before either of the two people who live here.', effects=exit_effects()),), ()),
)


def extend(initial, beats, exchanges, mixins, endings):
    for who in ("mara", "eli"):
        initial["people"][who].update(offenses=0, forgiven=0, heard=False, insight=False,
                                      commitment=False, privacy_breached=False, private_visited=False, willing_tell=False, private_silences=0)
    initial["people"]["player"].update(promises={"mara": False, "eli": False}, opened_floor=False,
                                      requested_separation=False, betrayal=False, witness_named=False)
    for who in ("mara", "eli", "player"):
        initial["people"][who]["knows"].update({fact: False for fact in (
            "mara_need", "eli_need", "mara_fear", "eli_fear", "refund", "schedule", "future")})
    initial["people"]["mara"]["knows"].update(mara_need=True, mara_fear=True, schedule=True)
    initial["people"]["eli"]["knows"].update(eli_need=True, eli_fear=True, refund=True)
    for name, owner, location, state in (
        ("soup", "eli", "kitchen", "warm"), ("mug", "couple", "kitchen", "empty"),
        ("calendar", "couple", "kitchen", "blank"), ("phone", "couple", "table", "quiet"),
        ("budget", "couple", "table", "blank"), ("brush_roll", "mara", "bedroom", "closed"),
        ("address", "mara", "sideboard", "blank"), ("chairs", "couple", "table", "apart")):
        initial["props"][name] = {"owner": owner, "location": location, "state": state}
    for who in ("mara", "eli"):
        key = "empathize " + who
        original = exchanges[key]
        text = ('Mara: "I want to say something without having to defend it before I have finished."',
                'Eli: "All right. I will wait until you have finished."') if who == "mara" else (
                'Eli: "I keep reaching for a joke because I don\'t know what my face looks like when I am afraid."',
                'Mara: "You can just look afraid. I know that face."')
        variant = replace(original.variants[0], lines=text,
                          effects=original.variants[0].effects + (E("set", "people." + who + ".heard", True),))
        exchanges[key] = replace(original, variants=(variant,), memory="disclosure")
        exchanges["blame " + who] = replace(exchanges["blame " + who], memory="repeat")
    exchanges["apologize"] = replace(exchanges["apologize"], memory="offense")
    exchanges["open floor"] = Exchange("floor", "Invite the hosts to speak directly to each other while you listen.", (
        P("floor", 'You move your chair a little back from the table. "I can listen. You do not need to speak through me."',
          'Mara looks at Eli. He looks back, then down at his hands. For once, you do not fill the gap.',
          effects=(E("set", "people.player.opened_floor", True),)),))
    exchanges["plan refund"] = Exchange("refund", "Ask Eli to recover the refundable deposit before noon tomorrow.", (
        P("refund", 'You: "Can you call before noon tomorrow and recover the six hundred, without making Mara responsible for the loss?"',
          'Eli: "Yes. I made the payment. I will make the call, and I will tell the agent it is my decision."',
          'Mara: "That is something I can believe because I will be able to see whether it happens."',
          effects=(E("set", "people.eli.commitment", True), E("set", "people.eli.accountable", True),
                   E("add", "people.mara.trust_partner", 1))),),
        influences=(((C("people.eli.disclosed", "eq", True),), 2, "The payment is public"),
                    ((C("people.player.knows.refund", "eq", True),), 2, "The deadline and recoverable sum are known"),
                    ((C("people.eli.trust_player", "ge", 2), C("people.eli.memes.anger", "le", 5)), 2, "Eli can hear a practical request")),
        threshold=6, refusals=(P("refused", 'Eli: "Before you tell me what to do with the money, hear what happened and what the terms actually are."'),))
    exchanges["plan visit"] = Exchange("visit", "Ask Mara to agree on the first visit and to discuss further decisions.", (
        P("visit", 'You: "Could you put the first visit on the calendar, and agree to talk before deciding the rest?"',
          'Mara: "Yes. The break after six weeks. I should have let Eli into the planning instead of making him find out after it."',
          'Eli: "I can work with a date. And with being told when a date has to change."',
          effects=(E("set", "people.mara.commitment", True), E("set", "people.mara.accountable", True),
                   E("add", "people.eli.trust_partner", 1))),),
        influences=(((C("people.mara.disclosed", "eq", True),), 2, "The residency is public"),
                    ((C("people.player.knows.schedule", "eq", True),), 2, "The first break is known"),
                    ((C("people.mara.trust_player", "ge", 2), C("people.mara.memes.anger", "le", 5)), 2, "Mara can hear a practical request")),
        threshold=6, refusals=(P("refused", 'Mara: "I will not invent a date to make the room feel better. Ask me what the schedule allows."'),))
    exchanges["separate"] = Exchange("separation", "Ask whether separate futures would be more honest than promising to stay.", (
        P("separation", 'You: "You do not owe the past an answer about the rest of your lives. Is staying together still what both of you want?"',
          'Mara: "I think I have been asking for permission to leave a life, not just a city."',
          'Eli is quiet for a long time. "Then I don\'t want your return to be something you owe me."',
          'They agree to make the practical decisions when neither is trying to win this evening.',
          effects=(E("set", "people.player.requested_separation", True), E("set", "people.player.requested_space", False))),),
        influences=(((C("people.mara.accountable", "eq", True), C("people.eli.accountable", "eq", True)), 2, "Both own their choices"),
                    ((C("people.player.knows.future", "eq", True),), 2, "They have discussed what choosing means"),
                    ((C("people.mara.memes.anger", "le", 5), C("people.eli.memes.anger", "le", 5)), 2, "This is a considered choice, not an angry threat")),
        threshold=6, refusals=(P("refused", 'Mara: "Do not turn the next thirty years into a suggestion before we have spoken about tonight."',
                                  'Eli: "That is our decision to reach. Give us time to reach it."'),))
    mixins.update(MIXINS)
    all_beats = tuple(beats) + TOPICS + AFTERMATH + CRISES
    revised = []
    for beat in all_beats:
        if beat.id == "unlearning_gifts":
            beat = replace(beat, resume='Eli: "You were telling me what help would actually be useful."',
                           when=beat.when + (C("people.player.requested_separation", "eq", False),))
        if beat.id == "calendar_margin":
            first = beat.goals[0]
            variant = replace(first.variants[0], effects=first.variants[0].effects + (E("set", "props.calendar.location", "table"),))
            beat = replace(beat, goals=(replace(first, variants=(variant,)),) + beat.goals[1:])
        if beat.id == "decision":
            beat = replace(beat, resume='Eli checks the time. "It is getting late."', goals=(
                G("opening", P("privacy", 'Eli puts your glass on a tray. Mara looks toward the hall.',
                                when=(C("people.player.betrayal", "eq", True),)),
                  P("settled", 'Mara looks around the table. "We have done enough deciding for one evening."',
                    'Eli: "Yes. Now we have to live with what we have said."')),
                G("pause", P("space", 'Mara feels for her flat key in her pocket. "I am keeping this."',
                              'Eli: "Of course."', when=(C("people.player.requested_space", "eq", True),)),
                  P("pause", 'The hosts let the room grow quiet. You reach toward the back of your chair.')),
                G("last_chance", P("ready", 'Eli turns on the hall light. It falls across the floor between the table and the door.')),
            ))
        revised.append(beat)
    return tuple(revised), exchanges, mixins, ENDINGS
