from dependency_injector import containers, providers
from presentation.pages.main_page import MainPage
from core.agent import GUIAgent
from capabilities.perception.time_perception import TimePerception
from capabilities.reasoning.simple_planner import SimplePlanner
from capabilities.action.time_action import TimeAction
from interfaces.messaging import MessageBus


class Container(containers.DeclarativeContainer):
    """依赖注入容器"""

    config = providers.Configuration()

    # 消息总线
    message_bus = providers.Singleton(MessageBus)

    # 能力层组件
    time_perception = providers.Singleton(TimePerception)
    simple_planner = providers.Singleton(SimplePlanner)
    time_action = providers.Singleton(TimeAction)

    # 核心Agent
    agent = providers.Singleton(
        GUIAgent,
        planner=simple_planner,
        perception=time_perception,
        action=time_action,
        message_bus=message_bus,
        config=config.agent
    )

    # 展示层
    main_page = providers.Singleton(
        MainPage,
        agent=agent,
        message_bus=message_bus,
        config=config.ui
    )