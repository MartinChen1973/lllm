```mermaid
%%{ init : { "theme" : "default" } }%%
graph TD
    A[chatbot] -->|Invoke| B[tools]
    B -->|Return to| A
    A -->|Conditional| C{Tool Usage}
    C -->|Used| B
    C -->|Not Used| A
```

```mermaid
graph TD
    __start__ --> chatbot
    chatbot --> tools
    tools --> chatbot
    chatbot -.-> __end__
```

```mermaid
graph TD
    __start__ --> chatbot
    chatbot -.-> tools
    tools --> chatbot
    chatbot -.-> __end__
```
