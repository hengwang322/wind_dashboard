FROM public.ecr.aws/lambda/python:3.9
RUN yum -y update; yum clean all
COPY requirements.txt .
RUN pip install --no-cache -r requirements.txt
COPY scripts  ${LAMBDA_TASK_ROOT}/scripts
COPY models  ${LAMBDA_TASK_ROOT}/models
COPY app.py models.py data.py ${LAMBDA_TASK_ROOT}
CMD [ "app.handler" ]
