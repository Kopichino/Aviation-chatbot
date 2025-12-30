# 1. Use AWS Lambda Python 3.12 Base Image
FROM public.ecr.aws/lambda/python:3.12

# 2. Copy requirements first (Better caching)
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# 3. Install dependencies
# We use --no-cache-dir to keep the image small
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the backend code
COPY backend/ ${LAMBDA_TASK_ROOT}/backend/

# 5. Set the CMD to your handler
CMD [ "backend.main.handler" ]

# 6.Copy the templates code
COPY templates/ ${LAMBDA_TASK_ROOT}/templates/