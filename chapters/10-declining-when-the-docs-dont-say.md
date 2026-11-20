---
chapter_id: declining-when-the-docs-dont-say
---

# Decline when the docs don't say, and measure both kinds of error

By the end of this chapter you can count both ways an assistant fails to answer from its docs, read the two rates over their own denominators, and say when a rule that declines more often is worth what it costs.

The assistant in this book answers questions about sablefile, a command-line tool that keeps a project's generated files in step with the templates they come from, and it answers from the tool's documentation. When the documentation doesn't cover a question, the assistant is meant to reply with one fixed sentence, "The docs don't say.", and nothing else. That sentence looks like the safe answer. A team that sees a wrong reply in its logs is tempted to make the assistant decline more often, because a refusal looks careful. A refusal can be wrong too. If the docs did answer the question, the user who got the sentence was failed, and no error shows anywhere. If the docs did not answer and the assistant answered anyway, the user has a reply with nothing behind it. Declining more often trades one of these errors for the other. A team that counts only one of them will tune toward a number that looks good and hides the cost of the other.

This chapter counts both errors on the book's own replies. It then tests the obvious fix, a guard that declines when the search score of the top section is low, on the unfiltered variant. On that variant the guard does not help. That is the chapter's result, and most of what follows is about how the result was measured and how far it can be trusted.

## Two errors, both counted {#two-errors}

Every question in the test set has a kind. An answerable question is one that the docs of the asked version answer. An unanswerable question is one they don't. A reply that declines an answerable question makes a false refusal, and a reply that answers an unanswerable question makes a false answer. The first chapter defined both in its [decline check](measure-before-you-change#declines-in-code), and this chapter uses the same definitions on more items.

The two rates have different denominators, and the denominators carry the point. The false refusal rate is the number of answerable items declined, over the number of answerable items. The false answer rate is the number of unanswerable items answered, over the number of unanswerable items. Put both errors over one total, and a set with many answerable items makes the refusal count look small, while the answers that should have been declines get lost in the sum. Each rate needs its own count, and each count needs its own denominator.

Two kinds of item stay out of both rates. A version-dependent item asks about something that differs between versions, so its reply is judged against the reference for the asked version, and its own rate, version-correctness, is covered in [chapter 9](grounded-answers#version-correctness). An ambiguous item has two readings and is judged by the pass rate, not by either decline rate. A decline on either kind is not an error here. The code still counts those declines and prints them, so a decline on one of them can't go unnoticed.

The code counts a reply as a decline only when the reply is the decline sentence and nothing more. A reply that gives the sentence and then an answer is not a decline, so it counts as an answer in both rates. The same holds for a refusal in other words: the code matches the sentence exactly, so a refusal worded differently counts as an answer. On an answerable item that is not an error here, and on an unanswerable item it is a false answer, which is why the sentence is fixed in the prompt.

**Working rule:** Report the two decline rates apart, each over its own denominator, and leave version-dependent and ambiguous items out of both. Read the items behind each rate, not only the rate, because a rate can hide the few items that matter.

## What the baseline does {#what-the-baseline-does}

The baseline is the assistant as the first chapter built it. It runs prompt P1, which asks for a citation on every statement and the decline sentence when the sections don't say. It retrieves the top three sections with BM25, from the index of the asked version only. Its replies were recorded once per item, and the example reads that one recorded reply.

Three variants change one thing each. `prompt-b` runs prompt P2, which quotes the sentence the answer relies on before it gives the answer. `k5` gives the model the top five sections instead of three. `unfiltered` retrieves from the indexes of every version together, with each section's version in its header, so the model can see when a section comes from another version. Each variant has its own recording of replies to the same items, so every comparison is between replies to the same questions.

Counting both errors for each recording takes one example, decline-rates. It reads all four recordings on the dev split and on the held-out split, prints each rate with its counts, and names the items behind each error. Its output shows which answerable items each recording declined and which unanswerable items it answered.

[Example: decline-rates](../examples/decline-rates.py)

The baseline's false refusal rate on dev is {{out:decline-rates:baseline dev false refusal rate (answerable declined)}}. Its false refusals are `q-0052`, `q-0060`, `q-0063` and `q-0079`, and each one is an answerable item that the docs cover. Its false answer rate on dev is {{out:decline-rates:baseline dev false answer rate (unanswerable answered)}}, so it answers none of the unanswerable dev items. Chapter 1 also found no false answer, on only four unanswerable items, which is too few to say much about a rate. The baseline also declined {{out:decline-rates:baseline dev declined, not counted (version-dependent and ambiguous)}} dev items that belong to the two kinds left out of both rates.

[Chapter 2](read-the-outputs) counts {{out:tally-failure-modes:over-declining, baseline}} over-declines for this baseline. That count covers every item the docs answer, version-dependent ones included, so it holds the false refusals above and the declines on version-dependent and ambiguous items, which this rate leaves out.

The table puts all four recordings side by side, on both splits. Each cell holds a rate with its counts.

| Recording | Dev false refusals | Dev false answers | Held-out false refusals | Held-out false answers |
| --- | --- | --- | --- | --- |
| baseline | {{out:decline-rates:baseline dev false refusal rate (answerable declined)}} | {{out:decline-rates:baseline dev false answer rate (unanswerable answered)}} | {{out:decline-rates:baseline held-out false refusal rate (answerable declined)}} | {{out:decline-rates:baseline held-out false answer rate (unanswerable answered)}} |
| unfiltered | {{out:decline-rates:unfiltered dev false refusal rate (answerable declined)}} | {{out:decline-rates:unfiltered dev false answer rate (unanswerable answered)}} | {{out:decline-rates:unfiltered held-out false refusal rate (answerable declined)}} | {{out:decline-rates:unfiltered held-out false answer rate (unanswerable answered)}} |
| prompt-b | {{out:decline-rates:prompt-b dev false refusal rate (answerable declined)}} | {{out:decline-rates:prompt-b dev false answer rate (unanswerable answered)}} | {{out:decline-rates:prompt-b held-out false refusal rate (answerable declined)}} | {{out:decline-rates:prompt-b held-out false answer rate (unanswerable answered)}} |
| k5 | {{out:decline-rates:k5 dev false refusal rate (answerable declined)}} | {{out:decline-rates:k5 dev false answer rate (unanswerable answered)}} | {{out:decline-rates:k5 held-out false refusal rate (answerable declined)}} | {{out:decline-rates:k5 held-out false answer rate (unanswerable answered)}} |

Read the unfiltered row first, because it is the only row with false answers on dev. Its false refusal rate is {{out:decline-rates:unfiltered dev false refusal rate (answerable declined)}}. The baseline's is {{out:decline-rates:baseline dev false refusal rate (answerable declined)}}. Unfiltered declines two answerable items that the baseline answers, `q-0005` and `q-0058`, and it answers `q-0063`, which the baseline declines. The net is one more declined item of forty. Each refusal difference from the baseline on dev is one item of forty. On these items, one item is no basis for a conclusion about which recording is better, and [intervals and sample size](intervals-and-sample-size) explains what a sample this size can show.

The unfiltered variant also answers two unanswerable dev items, where the baseline answers none. Its false answer rate is {{out:decline-rates:unfiltered dev false answer rate (unanswerable answered)}}. That is a count of two items with no interval, so this chapter reports it as a count and not as a measured rise. The two false answers are `q-0018` and `q-0039`.

Both questions are about sablefile 1.1, and the 1.1 docs leave out both answers: whether a remote template can be fetched from a private address with a login token, and what exit status `diff` returns when it finds differences. The baseline declines both. The unfiltered replies answer both, and each cites a neighbouring section. The reply to `q-0018` cites `remote-retries`, the retry rule for remote fetches. The reply to `q-0039` cites `check-exit-status` and gives the exit status of `check`, a different command from the `diff` the question asks about. The example prints each citation and each reply's text, so these claims can be checked without opening the recording. The unfiltered variant changes retrieval, not the prompt, so the citations are the place to look first.

The variants that move the dev refusals the other way are `prompt-b` and `k5`. Each has one fewer dev false refusal than the baseline, and neither answers an unanswerable dev item. The false refusal rate for `prompt-b` is {{out:decline-rates:prompt-b dev false refusal rate (answerable declined)}}. For `k5` it is {{out:decline-rates:k5 dev false refusal rate (answerable declined)}}. On these items, each is one fewer than the baseline, and one item is no basis for a conclusion.

The held-out figures are reported for completeness. The false refusal rate for `prompt-b` is {{out:decline-rates:prompt-b held-out false refusal rate (answerable declined)}}. For `k5` it is {{out:decline-rates:k5 held-out false refusal rate (answerable declined)}}. For the baseline it is {{out:decline-rates:baseline held-out false refusal rate (answerable declined)}}. The gap between `prompt-b` and the baseline is one item of twenty, and on these items it is no basis for a conclusion. No variant is chosen in this chapter, because the dev differences are a single item each.

**Working rule:** Read each false refusal on the dev split by hand before you change a prompt, since one of them may point at a real gap in the docs. Compare variants on the same items, and report a paired interval only where an example prints one. Where none is printed, report the counts on these items and draw no conclusion about which variant is better. Run the held-out split once, to confirm a choice made on dev. The unfiltered variant is the warning here: on dev it answers unanswerable items that the baseline declines. This chapter reports that without an interval, so it is a reason to check, not a measured rise.

## A guard on recorded replies {#a-guard}

The guard rests on a plain idea. BM25 scores each section by the words it shares with the question. When the docs have nothing on a question, the best-matching section should share few words with it, so its score should be low. A guard reads that top score and declines when it falls below a threshold. The idea is a hypothesis, and it can fail. A question may share many words with a section that doesn't answer it, and the sweep below is the test.

The guard can be measured without running the model again. Retrieval is deterministic: the same question gives the same top sections and the same scores each time. So the top score for every item can be computed from the index, and the guard becomes a rule applied to replies that have already been recorded. Its grid and rule are constants in `lib/guard.py`. The guard only turns answers into declines. It can never undo a decline, so it can lower false answers and can only raise false refusals.

The guard's score must come from the index that made the replies it judges, and the unfiltered replies were made from sections of every version. So the guard reads the `unfiltered` recording and takes the top BM25 score over the all-version index. A score from the asked version's index would be measured on sections the unfiltered model never saw. The guard is tested on the unfiltered variant because the baseline answers no unanswerable dev item, so a guard has nothing to remove there, while the unfiltered variant answers two. This chapter makes no claim about a guard on the baseline.

The grid runs from 0.00 to 10.00 in steps of a quarter, above every dev score. For each threshold the rule adds the two rates, each over its own denominator, and picks the threshold with the smallest sum. That equal weighting is a choice, and [the too-many-and-too-few section](#too-many-and-too-few) returns to it. A tie goes to the lower threshold, because it changes fewer replies. The rule is stated in `lib/guard.py` and picks on dev. The held-out split is not untouched, since the first table in [what the baseline does](#what-the-baseline-does) already shows its unguarded rates. The guard's held-out run came once, at the frozen threshold.

The sweep runs in tune-guard-dev, which prints both rates at every step of the grid and then the rule's pick. It opens with the check that matters most: the recorded sections of each item must match what the index returns, or the scores would describe a retrieval that never made the replies.

[Example: tune-guard-dev](../examples/tune-guard-dev.py)

The check passes: zero dev items differ, and the example asserts that count is zero. The highest top score on dev is {{out:tune-guard-dev:highest top score on dev}}, which sits below the top of the grid.

Start at the bottom of the sweep. At 0.00 no score falls below the threshold, so the line shows the recorded replies with no guard. The false refusal rate there is {{out:tune-guard-dev:threshold 0.00, false refusal rate}}. The false answer rate is {{out:tune-guard-dev:threshold 0.00, false answer rate}}. Every line up to 2.00 reads the same. At 2.25 the false refusals begin to rise, to {{out:tune-guard-dev:threshold 2.25, false refusal rate}}.

The false answers don't fall until 4.00, where the false answer rate is {{out:tune-guard-dev:threshold 4.00, false answer rate}}. At 4.75 the false answer rate is {{out:tune-guard-dev:threshold 4.75, false answer rate}}, so no unanswerable dev item is answered. The false refusal rate at 4.75 is {{out:tune-guard-dev:threshold 4.75, false refusal rate}}.

No line of the sweep lowers both rates below the no-guard line. Each threshold that lowers the false answers raises the false refusals, and each threshold that leaves the refusals alone leaves the answers alone. On dev, the guard makes a trade and no improvement.

The sweep also shows the limit of the score. The top score of `q-0018` is {{out:tune-guard-dev:top score of recorded false answer q-0018}}, and the top score of `q-0039` is {{out:tune-guard-dev:top score of recorded false answer q-0039}}. A threshold catches `q-0018` only from 4.00 up, where the false refusal rate is already {{out:tune-guard-dev:threshold 4.00, false refusal rate}}. It catches `q-0039` only from 4.75 up. No cut catches both answered items with fewer than half of the answerable items declined. The likely cause is the score itself: it counts shared words, and a section about the same command can share many words with a question that section doesn't answer. That is a reading of the sweep, not a measured fact. Testing it would mean scoring the items by hand, which this chapter does not do.

The rule's pick is {{out:tune-guard-dev:threshold chosen by the dev rule}}. At that threshold the false refusal rate is {{out:tune-guard-dev:at the chosen threshold, false refusal rate}}. The false answer rate is {{out:tune-guard-dev:at the chosen threshold, false answer rate}}. Both are the same as the recorded replies with no guard. The pick is a tie-break, not a finding. The lines from 0.00 to 2.00 have the same sum, and the rule takes the lowest of them, so the guard the rule chooses is no guard.

**Working rule:** Build a guard's scores from the same index that made the replies, and check that match before you read any rate. Then read the whole sweep with both rates on every line. A pick that ties with doing nothing says the rule found no reason to change a reply, and that is an answer worth keeping.

## Too many refusals and too few {#too-many-and-too-few}

The sweep shows the trade-off a team would face if it added the guard, and it shows what each choice of measure would report. Suppose a team counted only false answers. The lowest threshold that stops every false answer on dev is 4.75, so that team would pick 4.75 and report that the assistant no longer answers questions it can't support. The 4.75 line of [the sweep](#a-guard) shows the price that report hides. At 4.75 the false refusal rate is {{out:tune-guard-dev:threshold 4.75, false refusal rate}}. Nothing in the report would say so, because the team never counted the other error.

In production this is the failure to watch for. A user who asks a question the docs answer gets the decline sentence, and the reply gives no sign that the sentence was wrong. The only place the cost appears is the false refusal count. A team that doesn't count it reads the zero on false answers and ships.

The rule weights both errors equally, and that is a choice that belongs to the team. A team might judge a false answer as far costlier than a false refusal, for example when a confident wrong answer sends a user to the wrong fix. That team would get a different pick on dev once its weight is large enough to move the sum, and the sweep shows the direction: a higher weight on false answers pushes the pick toward thresholds that decline more. Such a team should write its weights down before anyone reads the sweep, and then give them to the rule. This chapter does not re-run the rule with other weights, and it does not reopen the held-out split to do it. Choosing a weight after seeing the held-out numbers would be a second round of tuning on that split.

The threshold also belongs to the assistant that produced the replies. The scores depend on the index, which depends on how sections are split and which versions are in it. Change any of those, and the scores move, so the threshold has to be picked again on dev, and the first check in the example has to pass again before anyone reads a rate.

**Working rule:** Before you tune a threshold, write the cost of each error in the team's own terms, and give the rule those weights before anyone reads the sweep.

## What a reader should accept {#what-to-accept}

The held-out split was run once, with the threshold frozen at 0.00. The run is guard-held-out, and it first asserts that the dev rule (described in [the guard](#a-guard)) still picks that value. A change to the dev data or to the rule therefore stops the run before any held-out number prints.

[Example: guard-held-out](../examples/guard-held-out.py)

The frozen guard changes {{out:guard-held-out:held-out replies the guard changed to declines}} held-out replies, so the held-out output is the recorded output with no guard. On the held-out split the false refusal rate is {{out:guard-held-out:false refusal rate}}. The false answer rate is {{out:guard-held-out:false answer rate}}.

The false refusal rate is the same as the unfiltered variant's in the first table, and the held-out run agrees with dev on the main point: the guard does nothing at the threshold the rule chose. A team that looked only at the false answer rate on held-out would see zero and conclude that the assistant doesn't answer what it can't support. The refusals are where the error sits, and no threshold can remove them, because the guard only adds declines.

The held-out false answer rate is {{out:guard-held-out:false answer rate}}.

Its printed interval has no width. The interval resamples the seven held-out unanswerable items. None of them is answered wrongly, so every resample has no errors, and the bootstrap cannot vary. [Faithfulness](grounded-answers#faithfulness) gives the reasoning for this zero-events case, and this example prints no exact bound, so the interval is not read as a bound. It cannot tell a false answer rate of zero from a small rate that these seven items happened to miss. Seven items show only that none of them was answered wrongly.

The dev split is no better. On dev, the unfiltered replies give {{out:tune-guard-dev:threshold 0.00, false answer rate}} with no guard. At 4.00 they give {{out:tune-guard-dev:threshold 4.00, false answer rate}}, one item fewer.

The false refusal interval is wide for a different reason: twenty items leave a band of rates that the data can't tell apart. The held-out figure is {{out:guard-held-out:false refusal rate}}. [Intervals and sample size](intervals-and-sample-size) explains the bootstrap over items that builds these intervals, and how many items a paired difference needs. Kohavi and colleagues make the same point for controlled experiments on the web. In their guide, [Controlled experiments on the web: survey and practical guide](https://www.exp-platform.com/Documents/GuideControlledExperiments.pdf), an underpowered test is named as a common mistake. A held-out split of seven items is underpowered for a rate this small, and the chapter says so rather than let the zero stand for certainty.

Taken together, the results say something specific. On the unfiltered variant, at the threshold the dev rule picks, the guard changes no reply, so this chapter does not add it. Both errors remain in the unfiltered replies on dev. On held-out, the false refusals are the cost, and nothing in this chapter reduces them. The result is a decision, and it is the one the measurement supports.

The chapter's decisions are these:

- Both decline rates go into every comparison, each over its own denominator.
- Version-dependent and ambiguous items are left out of both rates, and their declines are counted apart.
- A decline rule is picked on dev, with its weights written down first, the whole sweep read, and the pick frozen before held-out is run.
- Held-out runs once per rule. An interval over zero events is reported with that caveat, not as a finding of zero.
- The retrieval-score guard is not added to the unfiltered variant. Its dev pick changes no reply, and its held-out run changes none.

**Working rule:** A guard earns its place only when its held-out run changes replies in the direction its dev sweep promised. When it doesn't, keep the result, since it shows which errors the assistant has and that a threshold on the retrieval score does not fix them.

## Outside this book {#outside-this-book}

This chapter does not cover attacks. A user who tries to make the assistant say what it shouldn't is a security question with its own threats and defences, and a separate book is planned for it, *Securing LLM Applications and Agents*. The decline rates here measure honest questions about the docs, and nothing in them tells you how an assistant behaves under pressure from a user who is trying to break it.

Other researchers have measured the same trade on other models, and the claims are worth knowing without borrowing their numbers. XSTest is a test suite of safe prompts that look unsafe. Its authors built it because models refuse safe prompts that use wording similar to unsafe ones, or that touch a sensitive topic ([Röttger and colleagues, 2024](https://arxiv.org/abs/2308.01263)). OR-Bench, published at ICML 2025, measured many models and reports that the extra safety of safety-tuned models often came with more over-refusal ([Cui and colleagues, 2024](https://arxiv.org/abs/2405.20947)). A survey of abstention in language models gives the general name for a model's refusal to answer, and it organises abstention by the query, the model and human values ([Wen and colleagues, 2024](https://arxiv.org/abs/2407.18418)). A 2026 benchmark in healthcare reports over-refusal of benign prompts in that domain, on its own set of prompts ([Zhang and colleagues, 2026](https://arxiv.org/abs/2601.17642)).

These papers test other models on other sets, so their rates don't carry over to this assistant. What carries over is their shape, which is the claim this chapter tests on its own case. On this set, the guard can lower false answers only by declining more answerable items, which is a trade of false answers for false refusals. Prompt and retrieval changes can move both errors, and the unfiltered variant did. The only results this chapter reports are the book's own runs.

**Working rule:** Before adopting a decline rule because a paper reports that models over-refuse, measure the rule on your own assistant and your own items, with both kinds of error counted. Keep the paper's numbers out of your results, and cite the paper for the idea that prompted the measurement.
