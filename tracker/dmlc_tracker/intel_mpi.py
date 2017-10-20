"""
DMLC submission script, MPI version
"""
# pylint: disable=invalid-name
from __future__ import absolute_import

import sys
import subprocess, logging
from threading import Thread
from . import tracker

def get_intel_mpi_env(envs):
    """get the mpirun command for setting the envornment
    support both openmpi and mpich2
    """

    # windows hack: we will use msmpi
    if sys.platform == 'win32':
        for k, v in envs.items():
            cmd += ' -env %s %s' % (k, str(v))
        return cmd

    # decide MPI version.
    (out, _) = subprocess.Popen('mpirun',
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE).communicate()
    cmd = ''
    if 'Intel' in out:
        for k, v in envs.items():
            cmd += ' -env %s %s' % (k, str(v))
    else:
        raise RuntimeError('Unknown MPI Version')
    return cmd


def submit(args):
    """Submission script with MPI."""
    def intel_mpi_submit(nworker, nserver, pass_envs):
        """Internal closure for job submission."""
        def run(prog):
            """run the program"""
            subprocess.check_call(prog, shell=True)

        cmd = ''
        if args.host_file is not None:
            cmd = '-f %s ' % (args.host_file)
        cmd += ' ' + ' '.join(args.command)

        pass_envs['DMLC_JOB_CLUSTER'] = 'mpi'

        # start workers
        if nworker > 0:
            logging.info('Start %d workers by mpirun' % nworker)
            pass_envs['DMLC_ROLE'] = 'worker'
            if sys.platform == 'win32':
                prog = 'mpiexec -n %d %s %s' % (nworker, get_intel_mpi_env(pass_envs), cmd)
            else:
                prog = 'mpirun -n %d %s %s' % (nworker, get_intel_mpi_env(pass_envs), cmd)
            logging.info('Cmd: %s' % prog)
            thread = Thread(target=run, args=(prog,))
            thread.setDaemon(True)
            thread.start()
            logging.info('Workers started')


        # start servers
        if nserver > 0:
            logging.info('Start %d servers by mpirun' % nserver)
            pass_envs['DMLC_ROLE'] = 'server'
            if sys.platform == 'win32':
                prog = 'mpiexec -n %d %s %s' % (nserver, get_intel_mpi_env(pass_envs), cmd)
            else:
                prog = 'mpirun -n %d %s %s' % (nserver, get_intel_mpi_env(pass_envs), cmd)
            logging.info('Cmd: %s' % prog)
            thread = Thread(target=run, args=(prog,))
            thread.setDaemon(True)
            thread.start()
            logging.info('Servers started')


    tracker.submit(args.num_workers, args.num_servers,
                   fun_submit=intel_mpi_submit,
                   pscmd=(' '.join(args.command)))
