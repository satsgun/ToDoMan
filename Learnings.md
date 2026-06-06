# Learnings from Using Claude Code

1. **Provide all necessary details in the prompt.** Being verbose initially is helpful. A high-level overview of what you are trying to accomplish creates the necessary context for Claude Code.

2. **Break down the project into high-level stories and tasks where possible.** Ensure each story or task is highly granular. Take your time with the breakdown — it pays off later.

3. **Provide each granular story or task to Claude Code and iterate if needed.** The goal is to keep each commit small and digestible, meaning each commit will have changes that can be glanced over and understood quickly.

4. **Depending on the size of the project, this may result in a large number of commits — and that's exactly what you want.** Driving Claude Code through a complete project should feel comfortable and unhurried.

5. **Maintaining an up-to-date test suite and test harness helps catch bugs early and makes debugging easier later.**

6. **Integrating Claude Code into GitHub Actions is very helpful.** It may take some time to get working initially, but the effort is well worth it.

7. **With Claude Code integrated into GitHub Actions, you can have Claude review code, automatically create issues based on the review, invoke Claude to implement fixes, create a pull request, merge it, and finally close the issues.** Note: the full automated loop requires explicitly instructing Claude not to ask for confirmation at each step — otherwise it will pause and wait for your input between actions.
