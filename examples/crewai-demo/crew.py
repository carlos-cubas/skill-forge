"""
Customer Support Crew - CrewAI Demo with SkillForge Skills

This module demonstrates a three-agent customer support crew using SkillForge
skills to enhance agent capabilities. It validates:

1. Multi-agent coordination in CrewAI
2. Different skill injection modes (progressive vs inject)
3. Tool bundling with skills (ticket-creation, knowledge-search)
4. Skill discovery from shared-skills directory

Architecture:
- Router Agent (progressive mode): Uses greeting skill, routes to specialist
- Specialist Agent (inject mode): Uses troubleshooting + knowledge-search skills
- Escalation Agent (inject mode): Uses ticket-creation skill with bundled tool
"""

from crewai import Crew, Task

from skillforge.crewai import Agent


class CustomerSupportCrew:
    """Customer support crew with three specialized agents.

    This crew demonstrates SkillForge integration with CrewAI using
    shared skills from the examples/shared-skills directory.

    Agents:
        - Router: First contact, greets customer, routes to appropriate specialist
        - Specialist: Technical support for troubleshooting and knowledge lookup
        - Escalation: Creates tickets for unresolved issues

    Example:
        >>> crew = CustomerSupportCrew()
        >>> result = crew.crew().kickoff()
    """

    def router_agent(self) -> Agent:
        """Create the customer support router agent.

        Uses the greeting skill in progressive mode, meaning the meta-skill
        is injected and the agent can load full skill content on-demand
        via the `skillforge read` command.

        Returns:
            Agent configured as first-line support router.
        """
        return Agent(
            role="Customer Support Router",
            goal="Welcome customers warmly and route them to the right support path",
            backstory=(
                "You are a friendly first-line support agent who excels at making "
                "customers feel welcome and understood. You quickly assess customer "
                "needs and route them to the appropriate specialist."
            ),
            skills=["greeting"],
            skill_mode="progressive",
            allow_delegation=True,
            verbose=True,
        )

    def specialist_agent(self) -> Agent:
        """Create the technical support specialist agent.

        Uses troubleshooting and knowledge-search skills in inject mode,
        meaning the full skill content is injected into the agent's backstory.
        The knowledge-search skill includes a bundled `search_kb` tool.

        Returns:
            Agent configured as technical troubleshooter.
        """
        return Agent(
            role="Technical Support Specialist",
            goal="Diagnose and resolve technical issues efficiently using structured troubleshooting",
            backstory=(
                "You are an expert troubleshooter with deep knowledge of common "
                "technical issues. You follow systematic diagnosis procedures and "
                "leverage the knowledge base to find solutions quickly."
            ),
            skills=["troubleshooting", "knowledge-search"],
            skill_mode="inject",
            verbose=True,
        )

    def escalation_agent(self) -> Agent:
        """Create the escalation specialist agent.

        Uses the ticket-creation skill in inject mode. This skill includes
        a bundled `create_ticket` tool for creating support tickets.

        Returns:
            Agent configured for ticket creation and escalation.
        """
        return Agent(
            role="Escalation Specialist",
            goal="Create comprehensive support tickets for issues that need follow-up",
            backstory=(
                "You are a ticket management expert who ensures no customer issue "
                "falls through the cracks. You capture all relevant information and "
                "set appropriate priority levels for follow-up."
            ),
            skills=["ticket-creation"],
            skill_mode="inject",
            verbose=True,
        )

    def route_task(self, agent: Agent, customer_message: str) -> Task:
        """Create a task for routing the customer.

        Args:
            agent: The router agent to assign the task to.
            customer_message: The initial customer message.

        Returns:
            Task for greeting and routing the customer.
        """
        return Task(
            description=(
                f"A customer has reached out with the following message:\n\n"
                f'"{customer_message}"\n\n'
                "Your job is to:\n"
                "1. Greet the customer warmly using your greeting skill\n"
                "2. Understand their needs\n"
                "3. Determine if they need technical support or escalation\n\n"
                "Follow the greeting skill output format exactly."
            ),
            expected_output=(
                "A warm greeting following the greeting skill format, plus "
                "a brief assessment of the customer's needs and recommended "
                "next steps (technical support or escalation)."
            ),
            agent=agent,
        )

    def diagnose_task(self, agent: Agent, issue_description: str) -> Task:
        """Create a task for diagnosing a technical issue.

        Args:
            agent: The specialist agent to assign the task to.
            issue_description: Description of the technical issue.

        Returns:
            Task for troubleshooting and diagnosis.
        """
        return Task(
            description=(
                f"Diagnose and resolve the following technical issue:\n\n"
                f'"{issue_description}"\n\n'
                "Your job is to:\n"
                "1. Search the knowledge base for relevant articles\n"
                "2. Follow the troubleshooting skill's diagnosis framework\n"
                "3. Document each step and finding\n"
                "4. Provide a resolution or recommend escalation\n\n"
                "Follow the troubleshooting skill output format exactly."
            ),
            expected_output=(
                "A complete troubleshooting report following the skill format:\n"
                "- Problem statement\n"
                "- Diagnosis steps with results\n"
                "- Resolution or escalation recommendation"
            ),
            agent=agent,
        )

    def escalate_task(self, agent: Agent, issue_summary: str) -> Task:
        """Create a task for creating an escalation ticket.

        Args:
            agent: The escalation agent to assign the task to.
            issue_summary: Summary of the issue requiring escalation.

        Returns:
            Task for ticket creation.
        """
        return Task(
            description=(
                f"Create a support ticket for the following unresolved issue:\n\n"
                f'"{issue_summary}"\n\n'
                "Your job is to:\n"
                "1. Determine the appropriate priority level\n"
                "2. Create a clear, descriptive title\n"
                "3. Write a comprehensive description\n"
                "4. Use the create_ticket tool to submit\n"
                "5. Communicate the ticket details to the customer\n\n"
                "Follow the ticket-creation skill output format exactly."
            ),
            expected_output=(
                "A ticket creation report following the skill format:\n"
                "- Ticket ID (from the create_ticket tool)\n"
                "- Summary\n"
                "- Priority level and justification\n"
                "- Next steps for the customer"
            ),
            agent=agent,
        )

    def crew(
        self,
        customer_message: str = "Hi, I'm having trouble logging into my account",
        issue_description: str = "Customer cannot log in - password reset not working",
        issue_summary: str = "Login issue persists after password reset attempts",
    ) -> Crew:
        """Assemble the customer support crew with tasks.

        Args:
            customer_message: Initial customer message for routing.
            issue_description: Technical issue for diagnosis.
            issue_summary: Issue summary for ticket creation.

        Returns:
            Configured Crew ready to execute.
        """
        # Create agents
        router = self.router_agent()
        specialist = self.specialist_agent()
        escalation = self.escalation_agent()

        # Create tasks
        route = self.route_task(router, customer_message)
        diagnose = self.diagnose_task(specialist, issue_description)
        escalate = self.escalate_task(escalation, issue_summary)

        return Crew(
            agents=[router, specialist, escalation],
            tasks=[route, diagnose, escalate],
            verbose=True,
        )


def create_quick_crew() -> tuple[CustomerSupportCrew, Crew]:
    """Create a crew instance for quick validation.

    Returns:
        Tuple of (CustomerSupportCrew instance, assembled Crew).
    """
    support_crew = CustomerSupportCrew()
    crew = support_crew.crew()
    return support_crew, crew


if __name__ == "__main__":
    # Quick test - create crew and print agent info
    support_crew = CustomerSupportCrew()

    print("=== Customer Support Crew ===\n")

    print("Router Agent:")
    router = support_crew.router_agent()
    print(f"  Role: {router.role}")
    print(f"  Skills: {router.skills}")
    print(f"  Mode: {router.skill_mode}")
    print()

    print("Specialist Agent:")
    specialist = support_crew.specialist_agent()
    print(f"  Role: {specialist.role}")
    print(f"  Skills: {specialist.skills}")
    print(f"  Mode: {specialist.skill_mode}")
    print()

    print("Escalation Agent:")
    escalation = support_crew.escalation_agent()
    print(f"  Role: {escalation.role}")
    print(f"  Skills: {escalation.skills}")
    print(f"  Mode: {escalation.skill_mode}")
    print()

    print("Crew assembled successfully!")
