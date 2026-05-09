# Lambda-compatible image (AWS python3.11 base)
FROM public.ecr.aws/lambda/python:3.11

# System dependencies for rasterio / GDAL / netCDF
RUN yum install -y gdal gdal-devel netcdf netcdf-devel && yum clean all

WORKDIR ${LAMBDA_TASK_ROOT}

# Install Python dependencies
COPY lambda/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Lambda source
COPY lambda/ ./lambda/

# Default handler (override per function via CMD at deploy time)
CMD ["lambda.orchestration.pipeline_orchestrator.handler"]
