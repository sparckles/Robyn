## Architecture Design

Robyn is a Python web server that uses the tokio runtime.

First of all, we have a worker event cycle that basically does all the dirty work. This part manages the runtime and passes all instructions to the rust code.
This spawns the threading pool

Then when we type the command `python3 app.py` the python code is converted to rust objects and then the router is populated. The incoming requests hit the router and then the rust objects are dispatched in the thread pool and executed depending on their types

![Architecture](./assets/architecture/architecture.png)

Now, we can have multiple workers as well as multiple processes in Robyn. This allows the tcp socket to share itself across multiple cores.

![Multi Core Scaling](./assets/architecture/multi-processing.png)

## Const Requests

Const Requests is a feature that is unique to Robyn.

What if we could execute the function only once and store the response in the rust response. This would help us save a lot of overhead of calling the router.

![Const Request Optimisation Basis](./assets/architecture/const-request-optimisation-basis.png)

This is exactly what const requests tries to achieve.

![Const Request Optimisation](./assets/architecture/const-request-optimisation.png)

&nbsp;
&nbsp;
&nbsp;
&nbsp;
&nbsp;
&nbsp;

### Old architecture

![Diagram](https://i.ibb.co/cNV4DJX/image.png)

![Diagram of the final Architecture](https://i.ibb.co/GHwTTqk/Untitled-2021-02-25-0125-1.png)
